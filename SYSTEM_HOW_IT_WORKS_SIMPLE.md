# CodeMaster - How It Actually Works (Simple + With Code Locations)

This document explains **how** the system works (not just what exists), in simple language.
For every important flow, you get:
- What happens
- Where it happens (file path)
- Real code snippet from project

---

## 1. How the backend starts

### What happens
1. Flask app is created.
2. Config is loaded from environment.
3. Database/JWT/CORS/WebSocket extensions are attached.
4. All route modules are registered under `/api/...`.
5. Health endpoint is exposed.

### Code location
- `backend/app/__init__.py`
- `backend/run.py`

### Code
```python
# backend/app/__init__.py
def create_app(config_name=None):
    app = Flask(__name__)
    config_name = config_name or os.getenv('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, origins=app.config['CORS_ORIGINS'])
    sock.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.generator import generator_bp
    ...
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(generator_bp, url_prefix='/api/generator')
    ...
```

```python
# backend/run.py
app = create_app()
if __name__ == '__main__':
    app.run(host=host, port=port, debug=debug, use_reloader=debug, threaded=True)
```

---

## 2. How login/auth works

### What happens
1. Frontend sends email + password.
2. Backend checks user exists, not deleted, email verified, password valid.
3. Backend creates access + refresh JWT.
4. Frontend stores tokens and user in local/session storage.
5. For protected routes, middleware verifies token and loads `current_user`.

### Code location
- `backend/app/routes/auth.py`
- `backend/app/middleware/auth.py`
- `frontend/src/lib/api.ts`

### Code
```python
# backend/app/routes/auth.py
@auth_bp.route('/login', methods=['POST'])
def login():
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'Invalid email or password'}), 401
    if user.deleted_at:
        return jsonify({'error': 'Account deleted'}), 403
    if not bool(user.email_verified):
        return jsonify({'error': 'Please verify your email before logging in'}), 403
    if not user.check_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401

    access_token = create_access_token(identity=str(user.id), additional_claims={'pwd': _password_claim(user)})
    refresh_token = create_refresh_token(identity=str(user.id))
    return jsonify({'access_token': access_token, 'refresh_token': refresh_token, 'user': user.to_dict()})
```

```python
# backend/app/middleware/auth.py
def token_required(f):
    verify_jwt_in_request()
    current_user_id = get_jwt_identity()
    current_user = db.session.get(User, user_id)
    if not current_user:
        return jsonify({'error': 'Invalid or expired token'}), 401
```

```ts
// frontend/src/lib/api.ts
const data = await request("/auth/login", { method: "POST", body: JSON.stringify(payload) });
localStorage.setItem("access_token", data.access_token);
localStorage.setItem("refresh_token", data.refresh_token);
localStorage.setItem("user", JSON.stringify(data.user));
```

---

## 3. How token refresh works automatically

### What happens
1. Any API call goes through one shared `request()` function.
2. If backend returns 401/auth-expired, frontend calls `/auth/refresh`.
3. New access token is stored.
4. Original request is retried automatically.

### Code location
- `frontend/src/lib/api.ts`

### Code
```ts
async function request<T>(path: string, options: RequestInit = {}, allowRetry = true) {
  const res = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    const isAuthLikeError = res.status === 401 || loweredMessage.includes("invalid or expired token");
    if (isAuthLikeError && allowRetry && path !== "/auth/refresh") {
      const refreshed = await refreshAccessToken();
      const retryRes = await fetch(`${API_BASE_URL}${path}`, { ...options, headers: retryHeaders });
      ...
    }
  }
}
```

---

## 4. How compiler execution works

### What happens
1. User submits Java code from Compiler page.
2. Backend validates basic input and code length.
3. `JavaExecutor` compiles and runs code (Docker by default).
4. If errors exist, backend asks AI for fix suggestions.
5. Result is stored in `code_submissions`.
6. Response returns output/errors/timing/improvements.

### Code location
- `backend/app/routes/compiler.py`
- `backend/app/services/java_executor.py`

### Code
```python
# backend/app/routes/compiler.py
@compiler_bp.route('/execute', methods=['POST'])
@token_required
def execute_code(current_user):
    result = executor.compile_and_execute(java_code)
    if not result["success"] and result.get("errors"):
        ai_suggestions = ai_service.suggest_error_fix(...)
    submission = CodeSubmission(
        user_id=current_user.id,
        code=java_code,
        output=result.get("output", ""),
        status='success' if result["success"] else 'error'
    )
```

```python
# backend/app/services/java_executor.py
def compile_and_execute(self, java_code: str, input_data: str = "") -> Dict:
    if self.use_docker:
        result = self._execute_with_docker(java_code, input_data=input_data)
    else:
        result = self._execute_with_subprocess(java_code, input_data=input_data)
    return result
```

---

## 5. How terminal mode works (interactive Java run)

### What happens
1. Frontend calls `/compiler/terminal/start`.
2. Backend compiles code and creates a terminal session.
3. Backend returns websocket URL.
4. Frontend connects to `/ws/terminal`.
5. Input/output streams are bridged live.

### Code location
- `backend/app/routes/compiler.py`
- `backend/app/routes/terminal_ws.py`
- `backend/app/services/terminal_sessions.py`

### Code
```python
# backend/app/routes/compiler.py
result = manager.start_session(java_code, current_user.id)
ws_url = f"{ws_scheme}://{request.host}/ws/terminal?sessionId={result['session_id']}"
```

```python
# backend/app/routes/terminal_ws.py
@sock.route("/ws/terminal")
def terminal_socket(ws):
    session_id = request.args.get("sessionId")
    session = manager.get_session(session_id)
    ...
    # loop: send docker/local output to ws and ws input back to process
```

---

## 6. How AI code generation works

### What happens
1. User sends prompt from Generator page.
2. Backend stores user message in chat history.
3. AIService asks local RAG for Java code.
4. Output is sanitized/validated.
5. Assistant message is saved.
6. Skill points are deducted.

### Code location
- `backend/app/routes/generator.py`
- `backend/app/services/ai_service.py`
- `backend/app/models/generator_chat.py`

### Code
```python
# backend/app/routes/generator.py
db.session.add(GeneratorChatMessage(chat_id=chat.id, role='user', content=prompt))
generated_code = ai_service.generate_code(prompt, merged_context)
spent_ok, spent_error, remaining_points = consume_generation_points(current_user, prompt)
db.session.add(GeneratorChatMessage(chat_id=chat.id, role='assistant', content=generated_code, code=generated_code))
```

```python
# backend/app/services/ai_service.py
raw = rag.ask(query)
code = self._sanitize_generated_code(self._extract_code_snippet(raw) or raw)
if self._looks_like_java_code(code):
    return code
retry = rag.ask("Return only compilable Java code...")
```

---

## 7. How code explanation works

### What happens
1. User submits Java code on Explainer page.
2. Backend first does a **compile-only check**.
3. If compilation fails: returns guided correction message.
4. If compilation passes: calls AI explanation flow.

### Code location
- `backend/app/routes/explainer.py`
- `backend/app/services/java_executor.py`

### Code
```python
# backend/app/routes/explainer.py
executor = get_java_executor()
validation_result = executor.compile_only(java_code)
if compilation_errors:
    return jsonify({'message': 'Code validation failed', 'explanation': explanation}), 200
explanation = ai_service.explain_code(java_code)
```

---

## 8. How assessment works

### What happens
1. User starts assessment with level.
2. Backend builds a question set by type split (`mcq/msq/coding`).
3. Answers are submitted and scored.
4. Coding answers are evaluated via testcase execution.
5. Score and result metadata are stored.
6. User may accept level-up if eligible.

### Code location
- `backend/app/routes/assessment.py`
- `backend/app/services/assessment_service.py`
- `backend/app/models/assessment.py`

### Code
```python
# backend/app/services/assessment_service.py
QUESTION_SPLIT = {"mcq": 10, "msq": 10, "coding": 5}
def build_assessment_question_set(self, level: str) -> List[Question]:
    ...
```

```python
# backend/app/routes/assessment.py
score, result_meta = service.calculate_score(questions, answers)
assessment.score = score
assessment.completed_at = datetime.utcnow()
```

---

## 9. How practice validation works (important)

### What happens
1. User sends code + selected problem ID.
2. Backend loads problem testcases.
3. For each testcase, backend builds possible input variants.
4. Runs compile/execute.
5. Verifier checks output using generic and problem-specific rules.
6. Stores per-test result and final solved status.
7. Awards points if solved.

### Code location
- `backend/app/routes/practice.py`
- `backend/app/models/practice.py`
- `backend/app/services/skill_points_service.py`

### Code
```python
# backend/app/routes/practice.py
for candidate_input in input_variants:
    run = executor.compile_and_execute(code, input_data=candidate_input)
    actual_output = str(run.get('output', '')).strip()
    can_verify = bool(run.get('success')) or bool(actual_output)
    if can_verify and _verify_output(problem.title, candidate_input, actual_output, expected_output):
        success = True
        break
```

```python
# backend/app/routes/practice.py
# example of problem-specific verifier branch
if title == 'reverse an array':
    ...
    return out_ra[-len(arr_ra):] == list(reversed(arr_ra))
```

---

## 10. How points/rewards work

### What happens
1. Reward or deduction writes a transaction row.
2. User total points are updated in same operation.
3. Unique event key prevents duplicate reward for same action.

### Code location
- `backend/app/services/skill_points_service.py`
- `backend/app/models/skill_points.py`

### Code
```python
# backend/app/services/skill_points_service.py
def _apply_points(user, points_delta, event_type, event_key, event_data=None):
    user.total_points = max(0, int(user.total_points or 0) + int(points_delta))
    db.session.add(SkillPointTransaction(...))
```

```python
# backend/app/models/skill_points.py
__table_args__ = (
    db.UniqueConstraint("user_id", "event_type", "event_key", name="uq_skill_points_event"),
)
```

---

## 11. How profile security works

### What happens
- Password change and account deletion require CSRF header.
- Rate-limit is applied to prevent brute-force abuse.
- Account deletion anonymizes user and wipes linked personal data.

### Code location
- `backend/app/routes/profile.py`

### Code
```python
if not csrf_token or csrf_token != current_user.csrf_token:
    return jsonify({'error': 'Invalid CSRF token'}), 403
if not _check_rate_limit(rate_key, PASSWORD_UPDATE_LIMIT, PASSWORD_UPDATE_WINDOW_SECONDS, _password_update_attempts):
    return jsonify({'error': 'Too many password update attempts'}), 429
```

---

## 12. How content + learning path tracking works

### What happens
- Frontend fetches featured courses, learning paths, theory pages.
- Video completion awards points once.
- Course-open events are tracked for analytics/progress.

### Code location
- `backend/app/routes/content.py`

### Code
```python
@content_bp.route("/videos/complete", methods=["POST"])
def complete_video(current_user):
    awarded, points = award_video_points(current_user, video_key, normalized_level)
```

---

## 13. Frontend routing and API connection

### What happens
- `App.tsx` declares all routes/pages.
- `api.ts` is the single gateway to backend calls.
- Feature pages call domain clients (`authAPI`, `practiceAPI`, `compilerAPI`, etc.).

### Code location
- `frontend/src/App.tsx`
- `frontend/src/lib/api.ts`

### Code
```tsx
// frontend/src/App.tsx
<Route path="/compiler" element={<Compiler />} />
<Route path="/explainer" element={<Explainer />} />
<Route path="/generator" element={<Generator />} />
<Route path="/practice/solve/:level/:title" element={<PracticeSolve />} />
```

```ts
// frontend/src/lib/api.ts
export const generatorAPI = {
  async generateCode(prompt: string, language: string, chatId?: number | null) {
    return request("/generator/generate", { method: "POST", body: JSON.stringify({ prompt, language, chat_id: chatId ?? null }) });
  },
};
```

---

## 14. Database model map (simple)

Main tables and purpose:
- `users`: account, auth, profile
- `code_submissions`: compiler run history
- `questions`, `assessments`: assessment engine
- `practice_problems`, `practice_attempts`, `practice_drafts`: practice system
- `generator_chats`, `generator_chat_messages`: generator history
- `skill_point_transactions`: reward ledger
- `analytics_events`: behavior/activity tracking
- `user_settings`: editor/theme preferences
- content catalog tables: featured/learning/theory

### Core model locations
- `backend/app/models/user.py`
- `backend/app/models/code_submission.py`
- `backend/app/models/assessment.py`
- `backend/app/models/practice.py`
- `backend/app/models/generator_chat.py`
- `backend/app/models/skill_points.py`

---

## 15. Important config values (what they control)

Location:
- `backend/app/config.py`
- `backend/env.example`

Examples:
- `DATABASE_URL`: DB engine and connection
- `JWT_*`: token security and expiry
- `USE_DOCKER`, `JAVA_TIMEOUT`, `JAVA_MEMORY_LIMIT`: execution safety/performance
- `GOOGLE_*`, `GITHUB_*`: OAuth login
- `SMTP_*`: verification/reset/support email
- `TERMINAL_*`: interactive terminal limits

---

## 16. End-to-end flow summary (short)

1. User action in React page.
2. Page calls `api.ts` domain function.
3. `request()` adds JWT and handles refresh retries.
4. Flask route validates payload + auth.
5. Route calls service(s).
6. Service may call DB/AI/execution engine.
7. Route commits DB changes and returns JSON.
8. Frontend updates UI state and local/session caches.

---

## 17. Where to read next (fast navigation)

- App startup: `backend/app/__init__.py`
- Auth flow: `backend/app/routes/auth.py`
- Token middleware: `backend/app/middleware/auth.py`
- Compiler + terminal: `backend/app/routes/compiler.py`, `backend/app/routes/terminal_ws.py`
- Java engine: `backend/app/services/java_executor.py`
- Generator/explainer AI: `backend/app/services/ai_service.py`
- Practice verifier: `backend/app/routes/practice.py`
- Frontend API wiring: `frontend/src/lib/api.ts`
- Frontend route map: `frontend/src/App.tsx`

