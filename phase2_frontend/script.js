document.getElementById('budget-form').addEventListener('submit', function(event) {
    event.preventDefault();
    const income = parseFloat(document.getElementById('income').value);
    const expenses = parseFloat(document.getElementById('expenses').value);
    const results = document.getElementById('results');
    const balance = income - expenses;
    results.innerHTML = `<h3 class='text-lg font-bold'>Your Budget Result</h3><p>Balance: $${balance.toFixed(2)}</p>`;
});

document.getElementById('contact-form').addEventListener('submit', function(event) {
    event.preventDefault();
    alert('Your message has been sent!');
});