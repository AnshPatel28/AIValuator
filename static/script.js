document.addEventListener('DOMContentLoaded', function () {
    const app = document.getElementById('app');

    app.innerHTML = `
        <h1><i class="fas fa-graduation-cap"></i> Welcome to AIValuator</h1>
        <div class="form-group">
            <label for="numStudents">Enter Number of Students:</label>
            <input type="number" id="numStudents" required>
        </div>
        <div class="form-group">
            <label for="numQuestions">Enter Number of Questions:</label>
            <input type="number" id="numQuestions" required>
        </div>
        <div class="form-group">
            <button id="startButton"><i class="fas fa-play"></i> Start</button>
        </div>
        <div id="studentInputs"></div>
        <div id="questions"></div>
    `;

    document.getElementById('startButton').addEventListener('click', function () {
        const numStudents = document.getElementById('numStudents').value;
        const numQuestions = document.getElementById('numQuestions').value;
        const studentInputs = document.getElementById('studentInputs');
        const questionsDiv = document.getElementById('questions');

        studentInputs.innerHTML = '';
        questionsDiv.innerHTML = '';

        for (let i = 0; i < numStudents; i++) {
            studentInputs.innerHTML += `
                <div class="form-group">
                    <label for="student${i}">Enter Name of Student ${i + 1}:</label>
                    <input type="text" id="student${i}" required>
                </div>
            `;
        }

        for (let i = 0; i < numQuestions; i++) {
            questionsDiv.innerHTML += `
                <div class="form-group">
                    <label for="question${i}">Enter Question ${i + 1}:</label>
                    <input type="text" id="question${i}" required>
                    <label for="gptAnswer${i}">Enter GPT Answer ${i + 1}:</label>
                    <textarea id="gptAnswer${i}" rows="4" required></textarea>
                    <label for="textbookAnswer${i}">Enter Textbook Answer ${i + 1}:</label>
                    <textarea id="textbookAnswer${i}" rows="4" required></textarea>
                </div>
            `;

            for (let j = 0; j < numStudents; j++) {
                questionsDiv.innerHTML += `
                    <div class="form-group">
                        <label for="answer${i}_${j}">Enter Answer of Student ${j + 1} for Question ${i + 1}:</label>
                        <textarea id="answer${i}_${j}" rows="4" required></textarea>
                    </div>
                `;
            }
        }

        questionsDiv.innerHTML += `
            <div class="form-group">
                <button id="submitButton"><i class="fas fa-check"></i> Submit</button>
            </div>
        `;

        document.getElementById('submitButton').addEventListener('click', function () {
            const students = [];
            for (let i = 0; i < numStudents; i++) {
                students.push(document.getElementById(`student${i}`).value);
            }

            const questions = [];
            const gptAnswers = [];
            const textbookAnswers = [];
            const answers = [];

            for (let i = 0; i < numQuestions; i++) {
                const questionInput = document.getElementById(`question${i}`);
                const gptAnswerTextarea = document.getElementById(`gptAnswer${i}`);
                const textbookAnswerTextarea = document.getElementById(`textbookAnswer${i}`);
                const studentAnswerTextareas = [];

                for (let j = 0; j < numStudents; j++) {
                    studentAnswerTextareas.push(document.getElementById(`answer${i}_${j}`));
                }

                questions.push(questionInput.value);
                gptAnswers.push(gptAnswerTextarea.value);
                textbookAnswers.push(textbookAnswerTextarea.value);

                const questionAnswers = studentAnswerTextareas.map(textarea => textarea.value);
                answers.push(questionAnswers);
            }

            postData('/submit', { students, questions, answers, gpt_answers: gptAnswers, textbook_answers: textbookAnswers })
                .then(data => {
                    const combinedGrades = {};

                    for (const question in data) {
                        for (const student in data[question]) {
                            if (!combinedGrades[student]) {
                                combinedGrades[student] = { gpt: 0, textbook: 0 };
                            }
                            combinedGrades[student].gpt += data[question][student]['GPT'];
                            combinedGrades[student].textbook += data[question][student]['TextBook'];
                        }
                    }

                    app.innerHTML = `
                        <h1><i class="fas fa-star"></i> Graded Results</h1>
                        <div class="result">
                            ${Object.keys(data).map(question => `
                                <div>
                                    <h2>${question}</h2>
                                    <ul class="scores">
                                        ${Object.keys(data[question]).map(student => `
                                            <li>
                                                ${student}:
                                                <ul>
                                                    <li>GPT Marks: ${data[question][student]['GPT']}</li>
                                                    <li>TextBook Marks: ${data[question][student]['TextBook']}</li>
                                                </ul>
                                            </li>
                                        `).join('')}
                                    </ul>
                                </div>
                            `).join('')}
                            <h2>Combined Grades</h2>
                            <ul class="scores">
                                ${Object.keys(combinedGrades).map(student => `
                                    <li>
                                        ${student}:
                                        <ul>
                                            
                                            <li>GPT Marks: ${(combinedGrades[student].gpt / numQuestions).toFixed(2)}</li>
                                            <li>TextBook Marks: ${(combinedGrades[student].textbook / numQuestions).toFixed(2)}</li>
                                            
                                        </ul>
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                    `;
                });
        });
    });

    async function postData(url = '', data = {}) {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });
        return response.json();
    }
});
