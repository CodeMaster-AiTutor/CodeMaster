const fs = require('fs');
const path = require('path');

const levels = [
    {
        name: '🟢 BEGINNER',
        id: 'beginner',
        files: [
            {
                filename: 'hello-world.html',
                title: '1. Hello World',
                topics: ['Introduction to Java', 'Program Structure', 'main() method', 'Print Statements', 'Comments', 'Compilation & Execution']
            },
            {
                filename: 'variable.html',
                title: '2. Variables',
                topics: ['What is a Variable', 'int', 'double', 'boolean', 'char', 'String', 'Static Typing', 'Naming Rules']
            },
            {
                filename: 'input-output.html',
                title: '3. Input Output',
                topics: ['Scanner class', 'Taking integer input', 'Taking string input', 'Multiple inputs', 'Formatting output']
            },
            {
                filename: 'operators.html',
                title: '4. Operators',
                topics: ['Arithmetic operators', 'Assignment operators', 'Relational operators', 'Logical operators', 'Increment & Decrement']
            },
            {
                filename: 'conditionals.html',
                title: '5. Conditionals',
                topics: ['if statement', 'if-else', 'nested if', 'switch statement', 'real life decision examples']
            },
            {
                filename: 'loops.html',
                title: '6. Loops',
                topics: ['while loop', 'do-while loop', 'for loop', 'nested loops', 'break & continue']
            },
            {
                filename: 'methods.html',
                title: '7. Methods',
                topics: ['Why methods', 'Creating methods', 'Parameters', 'Return values', 'Method overloading']
            },
            {
                filename: 'arrays.html',
                title: '8. Arrays',
                topics: ['Array concept', 'Creating array', 'Iterating array', 'Searching', 'Min & Max']
            },
            {
                filename: 'strings.html',
                title: '9. Strings',
                topics: ['String basics', 'length()', 'equals()', 'substring()', 'toUpperCase()', 'string comparison']
            }
        ]
    },
    {
        name: '🟡 INTERMEDIATE',
        id: 'intermediate',
        files: [
            {
                filename: 'oop-intro.html',
                title: '10. OOP Intro',
                topics: ['Classes & Objects', 'Object creation', 'Fields & Methods', 'Real world modelling']
            },
            {
                filename: 'constructors.html',
                title: '11. Constructors',
                topics: ['Default constructor', 'Parameterized constructor', 'this keyword']
            },
            {
                filename: 'encapsulation.html',
                title: '12. Encapsulation',
                topics: ['private fields', 'getters & setters', 'data hiding', 'validation']
            },
            {
                filename: 'inheritance.html',
                title: '13. Inheritance',
                topics: ['parent & child class', 'extends keyword', 'method overriding', 'super keyword']
            },
            {
                filename: 'polymorphism.html',
                title: '14. Polymorphism',
                topics: ['runtime polymorphism', 'method overriding', 'dynamic binding']
            },
            {
                filename: 'abstraction.html',
                title: '15. Abstraction',
                topics: ['abstract class', 'abstract methods', 'interfaces', 'multiple inheritance via interface']
            },
            {
                filename: 'arraylist.html',
                title: '16. ArrayList',
                topics: ['Why ArrayList', 'add(), get(), remove()', 'iteration', 'dynamic resizing']
            },
            {
                filename: 'exception-handling.html',
                title: '17. Exception Handling',
                topics: ['try catch', 'multiple catch', 'finally', 'throw vs throws', 'custom exceptions']
            },
            {
                filename: 'file-handling.html',
                title: '18. File Handling',
                topics: ['Reading file', 'Writing file', 'BufferedReader', 'FileWriter']
            }
        ]
    },
    {
        name: '🔴 ADVANCED',
        id: 'advanced',
        files: [
            {
                filename: 'packages.html',
                title: '19. Packages',
                topics: ['Creating packages', 'import keyword', 'organizing projects']
            },
            {
                filename: 'collections.html',
                title: '20. Collections',
                topics: ['List', 'Set', 'Map', 'HashMap usage']
            },
            {
                filename: 'generics.html',
                title: '21. Generics',
                topics: ['Generic classes', 'Generic methods', 'type safety']
            },
            {
                filename: 'lambda.html',
                title: '22. Lambda',
                topics: ['Functional interfaces', 'Lambda expressions', 'forEach']
            },
            {
                filename: 'streams.html',
                title: '23. Streams',
                topics: ['Stream API', 'filter', 'map', 'reduce']
            },
            {
                filename: 'multithreading.html',
                title: '24. Multithreading',
                topics: ['Thread class', 'Runnable', 'synchronization', 'concurrency problems']
            },
            {
                filename: 'jdbc.html',
                title: '25. JDBC',
                topics: ['Database connection', 'executing queries', 'prepared statements']
            },
            {
                filename: 'serialization.html',
                title: '26. Serialization',
                topics: ['Saving objects', 'Reading objects', 'transient keyword']
            },
            {
                filename: 'mini-projects.html',
                title: '27. Mini Projects',
                topics: ['Student Management System', 'Bank System', 'File based storage', 'Menu driven programs']
            }
        ]
    }
];

function generateSidebar(currentFile) {
    let sidebarHtml = `<div class="sidebar">\n`;
    
    levels.forEach(level => {
        const isCurrentLevel = level.files.some(f => f.filename === currentFile);
        const displayStyle = isCurrentLevel ? 'block' : 'none';
        
        sidebarHtml += `    <div class="level">\n`;
        sidebarHtml += `        <div class="level-title" onclick="toggleLevel(this)">${level.name}</div>\n`;
        sidebarHtml += `        <div class="level-topics" style="display: ${displayStyle}">\n`;
        
        level.files.forEach(file => {
            const activeClass = file.filename === currentFile ? 'active' : '';
            sidebarHtml += `            <div class="topic">\n`;
            sidebarHtml += `                <a href="${file.filename}" class="topic-link ${activeClass}">${file.title}</a>\n`;
            
            if (file.filename === currentFile) {
                sidebarHtml += `                <div class="page-subtopics">\n`;
                file.topics.forEach(topic => {
                    const id = topic.toLowerCase().replace(/[^a-z0-9]+/g, '-');
                    sidebarHtml += `                    <a href="#${id}" class="subtopic-link">${topic}</a>\n`;
                });
                sidebarHtml += `                </div>\n`;
            }
            
            sidebarHtml += `            </div>\n`;
        });
        
        sidebarHtml += `        </div>\n`;
        sidebarHtml += `    </div>\n`;
    });
    
    sidebarHtml += `</div>\n`;
    return sidebarHtml;
}

function generateContent(file) {
    let contentHtml = `<div class="content">\n`;
    contentHtml += `    <h1>${file.title.split('. ')[1]}</h1>\n\n`;
    
    file.topics.forEach(topic => {
        const id = topic.toLowerCase().replace(/[^a-z0-9]+/g, '-');
        contentHtml += `    <h2 id="${id}">${topic}</h2>\n`;
        contentHtml += `    <p>This section covers ${topic}. Content will be added here.</p>\n`;
        contentHtml += `    <div class="code">\n// Example code for ${topic}\npublic class Example {\n    public static void main(String[] args) {\n        System.out.println("${topic}");\n    }\n}\n</div>\n`;
    });
    
    contentHtml += `</div>\n`;
    return contentHtml;
}

function generateHtml(file) {
    const sidebar = generateSidebar(file.filename);
    const content = generateContent(file);
    
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${file.title.split('. ')[1]} - Java Course</title>
    <link rel="stylesheet" href="style.css">
    <script src="script.js" defer></script>
</head>
<body>

    <!-- NAVBAR -->
    <div class="navbar">
        <div class="menu-btn">☰</div>
        <div class="logo">Java Course</div>
    </div>

    <div class="layout">
        ${sidebar}
        ${content}
    </div>

</body>
</html>`;
}

// Generate all files
levels.forEach(level => {
    level.files.forEach(file => {
        const html = generateHtml(file);
        fs.writeFileSync(path.join(__dirname, file.filename), html);
        console.log(`Generated ${file.filename}`);
    });
});
