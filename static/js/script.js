document.addEventListener('DOMContentLoaded', function() {
    // إخفاء الإشعارات بعد 4 ثوانٍ
    setTimeout(function() {
        let alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            let bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 4000);

    // البحث المباشر في صفحة القاموس
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            let filter = searchInput.value.toLowerCase();
            let cards = document.querySelectorAll('.term-container');
            
            cards.forEach(function(cardContainer) {
                let word = cardContainer.querySelector('.term-word').textContent.toLowerCase();
                let def = cardContainer.querySelector('.term-def').textContent.toLowerCase();
                
                if (word.includes(filter) || def.includes(filter)) {
                    cardContainer.style.display = ""; 
                } else {
                    cardContainer.style.display = "none"; 
                }
            });
        });
    }
});

// رسالة تأكيد للأدمن
function confirmAction(message) {
    return confirm(message);
}