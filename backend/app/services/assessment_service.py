"""Assessment service for managing Java assessments"""
import json
import random
import re
from typing import Dict, List, Tuple
from app.models.assessment import Question
from app.services.java_executor import get_java_executor

class AssessmentService:
    """Service for managing assessments and questions"""
    QUESTION_SPLIT = {"mcq": 10, "msq": 10, "coding": 5}
    MCQ_MARKS = 2
    MSQ_STANDARD_MARKS = 3
    MSQ_HIGH_MARKS = 4
    CODING_MARKS = 16
    CODING_COUNT_FOR_SCORING = 3

    def get_questions_for_level(self, level: str, count: int = 20) -> List[Question]:
        return Question.query.filter_by(difficulty=level).limit(count).all()

    def build_assessment_question_set(self, level: str) -> List[Question]:
        selected: List[Question] = []
        for q_type, required in self.QUESTION_SPLIT.items():
            pool = Question.query.filter_by(difficulty=level, question_type=q_type).all()
            if len(pool) < required:
                raise ValueError(f"Insufficient {q_type} questions for {level}. Need {required}, found {len(pool)}")
            selected.extend(random.sample(pool, required))
        random.shuffle(selected)
        return selected

    def calculate_score(self, questions: List[Question], answers: Dict[str, object]) -> Tuple[int, List[Dict]]:
        details: List[Dict] = []
        score_marks = 0
        mcq_questions = [q for q in questions if q.question_type == "mcq"]
        msq_questions = [q for q in questions if q.question_type == "msq"]
        coding_questions = [q for q in questions if q.question_type == "coding"]
        msq_high_mark_ids = {q.id for q in msq_questions[:2]}
        coding_correct_ids: List[int] = []
        coding_correct_map: Dict[int, bool] = {}

        for question in questions:
            user_answer = answers.get(str(question.id), answers.get(question.id, ""))
            is_correct = self._is_correct(question, user_answer)
            mark_weight = 0
            marks_awarded = 0
            selected_for_scoring = True
            if question.question_type == "mcq":
                mark_weight = self.MCQ_MARKS
                if is_correct:
                    marks_awarded = mark_weight
                    score_marks += marks_awarded
            elif question.question_type == "msq":
                mark_weight = self.MSQ_HIGH_MARKS if question.id in msq_high_mark_ids else self.MSQ_STANDARD_MARKS
                if is_correct:
                    marks_awarded = mark_weight
                    score_marks += marks_awarded
            elif question.question_type == "coding":
                mark_weight = self.CODING_MARKS
                coding_correct_map[question.id] = is_correct
                if is_correct:
                    coding_correct_ids.append(question.id)
                selected_for_scoring = False
            details.append({
                "question_id": question.id,
                "type": question.question_type,
                "is_correct": is_correct,
                "mark_weight": mark_weight,
                "marks_awarded": marks_awarded,
                "selected_for_scoring": selected_for_scoring
            })

        selected_coding_ids = set(coding_correct_ids[:self.CODING_COUNT_FOR_SCORING])
        for item in details:
            if item["type"] != "coding":
                continue
            question_id = item["question_id"]
            item["selected_for_scoring"] = question_id in selected_coding_ids
            item["marks_awarded"] = self.CODING_MARKS if question_id in selected_coding_ids else 0
        score_marks += len(selected_coding_ids) * self.CODING_MARKS

        total_possible_marks = (
            len(mcq_questions) * self.MCQ_MARKS
            + max(0, len(msq_questions) - 2) * self.MSQ_STANDARD_MARKS
            + min(2, len(msq_questions)) * self.MSQ_HIGH_MARKS
            + min(self.CODING_COUNT_FOR_SCORING, len(coding_questions)) * self.CODING_MARKS
        )
        percentage = int((score_marks / total_possible_marks) * 100) if total_possible_marks else 0
        return percentage, details

    def _is_correct(self, question: Question, user_answer: object) -> bool:
        if question.question_type == "mcq":
            return str(user_answer or "").strip() == str(question.correct_answer or "").strip()
        if question.question_type == "msq":
            expected = self._parse_json_list(question.correct_answer)
            selected = user_answer if isinstance(user_answer, list) else [item.strip() for item in str(user_answer or "").split(",") if item.strip()]
            expected_set = {str(x).strip() for x in expected}
            selected_set = {str(x).strip() for x in selected}
            return expected_set == selected_set
        if question.question_type == "coding":
            return self._validate_coding_answer(question, str(user_answer or ""))
        return str(user_answer or "").strip() == str(question.correct_answer or "").strip()

    def _parse_json_list(self, raw: str) -> List[str]:
        try:
            loaded = json.loads(raw or "[]")
            if isinstance(loaded, list):
                return [str(x) for x in loaded]
        except Exception:
            pass
        return [item.strip() for item in str(raw or "").split(",") if item.strip()]

    def _validate_coding_answer(self, question: Question, code: str) -> bool:
        if not code.strip():
            return False
        result = self.run_coding_test_cases(question, code)
        return bool(result.get("all_passed"))

    def _parse_question_payload(self, question: Question) -> Dict:
        try:
            payload = json.loads(question.correct_answer or "{}")
            if isinstance(payload, dict):
                return payload
        except Exception:
            pass
        return {}

    def _compare_output(self, actual: str, expected: str) -> bool:
        if actual.strip() == expected.strip():
            return True
        actual_compact = re.sub(r"\s+", " ", actual.strip())
        expected_compact = re.sub(r"\s+", " ", expected.strip())
        return actual_compact == expected_compact

    def run_coding_test_cases(self, question: Question, code: str) -> Dict:
        payload = self._parse_question_payload(question)
        raw_cases = payload.get("test_cases") if isinstance(payload, dict) else None
        test_cases = raw_cases if isinstance(raw_cases, list) else []
        if not test_cases:
            test_cases = [{"input": "", "output": "", "match_type": "compile_only"}]
        executor = get_java_executor()
        case_results = []
        passed = 0
        for index, case in enumerate(test_cases, start=1):
            expected_output = str((case or {}).get("output", ""))
            match_type = str((case or {}).get("match_type", "exact")).strip() or "exact"
            expected_keywords = (case or {}).get("expected_keywords", [])
            variants = self._build_input_variants((case or {}).get("input", ""))
            selected_output = ""
            selected_errors = []
            success = False
            if match_type == "compile_only":
                run = executor.compile_and_execute(code, input_data="")
                success = bool(run.get("success"))
                selected_output = str(run.get("output", ""))
                selected_errors = run.get("errors", []) if isinstance(run.get("errors", []), list) else []
            else:
                for candidate_input in variants:
                    run = executor.compile_and_execute(code, input_data=candidate_input)
                    selected_output = str(run.get("output", ""))
                    selected_errors = run.get("errors", []) if isinstance(run.get("errors", []), list) else []
                    if not run.get("success"):
                        continue
                    if self._verify_case_output(selected_output, expected_output, match_type, expected_keywords):
                        success = True
                        break
            if success:
                passed += 1
            case_results.append({
                "index": index,
                "input": str((case or {}).get("input", "")),
                "expected_output": expected_output,
                "actual_output": selected_output,
                "match_type": match_type,
                "success": success,
                "errors": selected_errors
            })
        return {
            "all_passed": passed == len(case_results),
            "passed": passed,
            "total": len(case_results),
            "results": case_results
        }

    def _build_input_variants(self, raw_input: object) -> List[str]:
        base = str(raw_input or "")
        normalized = base.replace("\r\n", "\n").replace("\r", "\n")
        variants = [normalized]
        if normalized and not normalized.endswith("\n"):
            variants.append(f"{normalized}\n")
        compact = normalized.strip()
        if compact and compact not in variants:
            variants.append(compact)
        return list(dict.fromkeys(variants))

    def _verify_case_output(self, actual: str, expected: str, match_type: str, expected_keywords: object) -> bool:
        actual_text = str(actual or "").strip()
        expected_text = str(expected or "").strip()
        if match_type == "contains":
            return expected_text.lower() in actual_text.lower()
        if match_type == "contains_keywords":
            keys = expected_keywords if isinstance(expected_keywords, list) else []
            filtered = [str(k).strip().lower() for k in keys if str(k).strip()]
            if not filtered:
                return expected_text.lower() in actual_text.lower()
            target = actual_text.lower()
            return all(key in target for key in filtered)
        return self._compare_output(actual_text, expected_text)

# Singleton instance
_assessment_service_instance = None

def get_assessment_service() -> AssessmentService:
    """Get singleton assessment service instance"""
    global _assessment_service_instance
    if _assessment_service_instance is None:
        _assessment_service_instance = AssessmentService()
    return _assessment_service_instance
