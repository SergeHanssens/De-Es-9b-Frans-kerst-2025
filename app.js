// Mala's French Learning App - Interactive JavaScript

// Topic names for display
const topicNames = {
    'pronoms-sujets': 'Les pronoms personnels sujets',
    'negation': 'La négation',
    'etre-avoir': 'Être / Avoir / Verbes -ER',
    'verbes-re': 'Les verbes en -RE',
    'verbes-ir': 'Les verbes en -IR',
    'questions': 'La question',
    'adj-possessif': "L'adjectif possessif",
    'adj-qualificatif': "L'adjectif qualificatif",
    'verbes-pronominaux': 'Les verbes pronominaux',
    'adj-demonstratif': "L'adjectif démonstratif",
    'article-partitif': "L'article partitif",
    'imparfait': "L'imparfait",
    'futur-simple': 'Le futur simple',
    'conditionnel': 'Le conditionnel',
    'cod-coi': 'Les pronoms COD / COI',
    'passe-compose': 'Le passé composé',
    'imperatif': "L'impératif",
    'futur-proche': 'Le futur proche'
};

// Initialize progress tracking
let progress = JSON.parse(localStorage.getItem('malaProgress')) || {};
let studySessions = JSON.parse(localStorage.getItem('malaStudySessions')) || [];

// Navigation
document.addEventListener('DOMContentLoaded', function() {
    // Navigation links
    document.querySelectorAll('[data-topic]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const topic = this.getAttribute('data-topic');
            showTopic(topic);
        });
    });

    // Option buttons for multiple choice
    document.querySelectorAll('.option-btn').forEach(btn => {
        btn.addEventListener('click', handleOptionClick);
    });

    // Check buttons for fill-in-the-blank
    document.querySelectorAll('.check-btn').forEach(btn => {
        btn.addEventListener('click', handleCheckClick);
    });

    // Reset progress button
    document.getElementById('reset-progress').addEventListener('click', resetProgress);

    // Study planner
    document.getElementById('add-session').addEventListener('click', addStudySession);

    // Initialize date input to today
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('study-date').value = today;

    // Load saved data
    updateProgressDisplay();
    renderStudySessions();
    markCompletedTopics();
});

// Show a specific topic section
function showTopic(topicId) {
    // Hide all sections
    document.querySelectorAll('.topic-section').forEach(section => {
        section.classList.remove('active');
    });

    // Show the selected section
    const targetSection = document.getElementById(topicId);
    if (targetSection) {
        targetSection.classList.add('active');
    }

    // Update progress display if showing progress page
    if (topicId === 'progress') {
        updateProgressDisplay();
    }

    // Scroll to top of content
    window.scrollTo({ top: 200, behavior: 'smooth' });
}

// Handle multiple choice option click
function handleOptionClick(e) {
    const btn = e.target;
    const exercise = btn.closest('.exercise');
    const options = exercise.querySelectorAll('.option-btn');
    const feedback = exercise.querySelector('.feedback');
    const isCorrect = btn.hasAttribute('data-correct');
    const topic = exercise.closest('.exercise-container').getAttribute('data-topic');
    const exerciseId = exercise.getAttribute('data-exercise-id');

    // Check if already answered
    if (exercise.classList.contains('correct') || exercise.classList.contains('incorrect')) {
        return;
    }

    // Disable all options
    options.forEach(opt => opt.disabled = true);

    // Mark selected and correct answers
    if (isCorrect) {
        btn.classList.add('selected-correct');
        exercise.classList.add('correct');
        feedback.textContent = '✅ Goed gedaan! Dat is correct!';
        feedback.className = 'feedback show correct';
        saveProgress(topic, exerciseId, true);
    } else {
        btn.classList.add('selected-incorrect');
        exercise.classList.add('incorrect');
        feedback.textContent = '❌ Helaas, dat is niet juist. Bekijk de theorie nog eens.';
        feedback.className = 'feedback show incorrect';

        // Show correct answer
        options.forEach(opt => {
            if (opt.hasAttribute('data-correct')) {
                opt.classList.add('show-correct');
            }
        });
        saveProgress(topic, exerciseId, false);
    }

    markCompletedTopics();
}

// Handle fill-in-the-blank check
function handleCheckClick(e) {
    const btn = e.target;
    const exercise = btn.closest('.exercise');
    const inputs = exercise.querySelectorAll('.blank-input');
    const feedback = exercise.querySelector('.feedback');
    const topic = exercise.closest('.exercise-container').getAttribute('data-topic');
    const exerciseId = exercise.getAttribute('data-exercise-id');

    // Check if already answered
    if (exercise.classList.contains('correct') || exercise.classList.contains('incorrect')) {
        return;
    }

    let allCorrect = true;

    inputs.forEach(input => {
        const answer = input.getAttribute('data-answer').toLowerCase();
        const userAnswer = input.value.trim().toLowerCase();

        if (userAnswer === answer) {
            input.classList.add('correct');
        } else {
            input.classList.add('incorrect');
            allCorrect = false;
            // Show correct answer
            input.value = input.getAttribute('data-answer');
        }
        input.disabled = true;
    });

    btn.disabled = true;

    if (allCorrect) {
        exercise.classList.add('correct');
        feedback.textContent = '✅ Goed gedaan! Dat is correct!';
        feedback.className = 'feedback show correct';
        saveProgress(topic, exerciseId, true);
    } else {
        exercise.classList.add('incorrect');
        feedback.textContent = '❌ Niet helemaal juist. De correcte antwoorden zijn nu ingevuld.';
        feedback.className = 'feedback show incorrect';
        saveProgress(topic, exerciseId, false);
    }

    markCompletedTopics();
}

// Save progress to localStorage
function saveProgress(topic, exerciseId, isCorrect) {
    if (!progress[topic]) {
        progress[topic] = {};
    }
    progress[topic][exerciseId] = isCorrect;
    localStorage.setItem('malaProgress', JSON.stringify(progress));
}

// Update progress display
function updateProgressDisplay() {
    let totalCorrect = 0;
    let totalExercises = 0;
    const topicScoresContainer = document.getElementById('topic-scores');
    topicScoresContainer.innerHTML = '';

    for (const topic in topicNames) {
        const topicProgress = progress[topic] || {};
        const exerciseCount = Object.keys(topicProgress).length;
        const correctCount = Object.values(topicProgress).filter(v => v === true).length;

        totalExercises += exerciseCount;
        totalCorrect += correctCount;

        if (exerciseCount > 0) {
            const percentage = Math.round((correctCount / exerciseCount) * 100);
            const item = document.createElement('div');
            item.className = 'topic-score-item';
            item.innerHTML = `
                <span class="name">${topicNames[topic]}</span>
                <span class="score">${correctCount}/${exerciseCount}</span>
                <div class="mini-progress">
                    <div class="mini-fill" style="width: ${percentage}%"></div>
                </div>
            `;
            topicScoresContainer.appendChild(item);
        }
    }

    // Update total score
    document.getElementById('total-correct').textContent = totalCorrect;
    document.getElementById('total-exercises').textContent = totalExercises;

    // Update progress bar
    const percentage = totalExercises > 0 ? Math.round((totalCorrect / totalExercises) * 100) : 0;
    document.getElementById('total-progress').style.width = percentage + '%';
}

// Mark completed topics in navigation
function markCompletedTopics() {
    for (const topic in progress) {
        const topicProgress = progress[topic];
        const exerciseCount = Object.keys(topicProgress).length;
        const correctCount = Object.values(topicProgress).filter(v => v === true).length;

        if (exerciseCount > 0 && correctCount === exerciseCount) {
            // Mark as completed in nav
            document.querySelectorAll(`[data-topic="${topic}"]`).forEach(link => {
                link.classList.add('completed');
            });
        }
    }
}

// Reset progress
function resetProgress() {
    if (confirm('Weet je zeker dat je alle voortgang wilt wissen? Dit kan niet ongedaan worden gemaakt.')) {
        progress = {};
        localStorage.removeItem('malaProgress');

        // Reset all exercises
        document.querySelectorAll('.exercise').forEach(exercise => {
            exercise.classList.remove('correct', 'incorrect');
            exercise.querySelectorAll('.option-btn').forEach(btn => {
                btn.disabled = false;
                btn.classList.remove('selected-correct', 'selected-incorrect', 'show-correct');
            });
            exercise.querySelectorAll('.blank-input').forEach(input => {
                input.disabled = false;
                input.value = '';
                input.classList.remove('correct', 'incorrect');
            });
            exercise.querySelectorAll('.check-btn').forEach(btn => {
                btn.disabled = false;
            });
            exercise.querySelector('.feedback').className = 'feedback';
        });

        // Reset nav completed markers
        document.querySelectorAll('.nav-section a').forEach(link => {
            link.classList.remove('completed');
        });

        updateProgressDisplay();
        alert('Je voortgang is gereset!');
    }
}

// Study Planner Functions
function addStudySession() {
    const date = document.getElementById('study-date').value;
    const topic = document.getElementById('study-topic').value;
    const duration = document.getElementById('study-duration').value;
    const notes = document.getElementById('study-notes').value;

    if (!date || !topic) {
        alert('Vul alsjeblieft een datum en onderwerp in!');
        return;
    }

    const session = {
        id: Date.now(),
        date: date,
        topic: topic,
        topicName: topicNames[topic] || topic,
        duration: parseInt(duration),
        notes: notes
    };

    studySessions.push(session);
    localStorage.setItem('malaStudySessions', JSON.stringify(studySessions));

    // Reset form
    document.getElementById('study-notes').value = '';

    renderStudySessions();
}

function deleteStudySession(id) {
    if (confirm('Weet je zeker dat je deze sessie wilt verwijderen?')) {
        studySessions = studySessions.filter(s => s.id !== id);
        localStorage.setItem('malaStudySessions', JSON.stringify(studySessions));
        renderStudySessions();
    }
}

function renderStudySessions() {
    const container = document.getElementById('session-list');
    container.innerHTML = '';

    // Sort by date (newest first)
    const sortedSessions = [...studySessions].sort((a, b) => new Date(b.date) - new Date(a.date));

    sortedSessions.forEach(session => {
        const item = document.createElement('div');
        item.className = 'session-item';
        item.innerHTML = `
            <div class="date">${formatDate(session.date)}</div>
            <div class="topic">${session.topicName}</div>
            <div class="duration">${session.duration} minuten</div>
            ${session.notes ? `<div class="notes">"${session.notes}"</div>` : ''}
            <button class="delete-btn" onclick="deleteStudySession(${session.id})">×</button>
        `;
        container.appendChild(item);
    });

    // Update summary
    document.getElementById('session-count').textContent = studySessions.length;
    const totalTime = studySessions.reduce((sum, s) => sum + s.duration, 0);
    document.getElementById('total-time').textContent = totalTime;

    // Check if requirement is met (8 sessions of 60 min)
    const validSessions = studySessions.filter(s => s.duration >= 60).length;
    if (validSessions >= 8) {
        document.querySelector('.log-info').innerHTML = '🎉 Je hebt de minimale vereiste gehaald!';
        document.querySelector('.log-info').style.color = '#27ae60';
    } else {
        document.querySelector('.log-info').innerHTML = `Minimaal 8 sessies van 1 uur nodig! (${validSessions}/8 compleet)`;
        document.querySelector('.log-info').style.color = '#666';
    }
}

function formatDate(dateString) {
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('nl-BE', options);
}

// Make deleteStudySession available globally
window.deleteStudySession = deleteStudySession;
