document.addEventListener('DOMContentLoaded', function() {
    // إخفاء الإشعارات بعد 4 ثوانٍ
    setTimeout(function() {
        let alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            if(typeof bootstrap !== 'undefined') {
                let bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } else {
                alert.style.display = 'none';
            }
        });
    }, 4000);

    // البحث المباشر في صفحة القاموس 
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            let filter = searchInput.value.toLowerCase();
            let rows = document.querySelectorAll('.term-row');
            
            rows.forEach(function(row) {
                // تحديث كلاسات البحث حسب الأعمدة الجديدة
                let englishTerm = row.querySelector('.en-term').textContent.toLowerCase();
                let arabicTerm = row.querySelector('.ar-term').textContent.toLowerCase();
                let definition = row.querySelector('.definition-desc').textContent.toLowerCase();
                let subject = row.querySelector('.subject-field').textContent.toLowerCase();
                
                if (englishTerm.includes(filter) || arabicTerm.includes(filter) || definition.includes(filter) || subject.includes(filter)) {
                    row.style.display = ""; 
                } else {
                    row.style.display = "none";
                }
            });
        });
    }
});

// تفعيل خاصية تحديد الكل (Select All) في جدول الأدمن
const selectAllCheckbox = document.getElementById('selectAll');
if (selectAllCheckbox) {
    selectAllCheckbox.addEventListener('change', function() {
        const checkboxes = document.querySelectorAll('.term-checkbox');
        checkboxes.forEach(cb => cb.checked = selectAllCheckbox.checked);
    });
}

function confirmAction(message) {
    return confirm(message);
}
