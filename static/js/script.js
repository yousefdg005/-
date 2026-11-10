function normalizeArabic(text) {
    if (!text) return '';
    return text
        .toLowerCase()
        .replace(/[\u064B-\u0652\u0670]/g, '') // إزالة التشكيل
        .replace(/[أإآ]/g, 'ا')
        .replace(/ى/g, 'ي')
        .replace(/ة/g, 'ه')
        .trim();
}

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

    // البحث المباشر في صفحة القاموس مع دعم تطبيع الحروف العربية
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            let filter = normalizeArabic(searchInput.value);
            let rows = document.querySelectorAll('.term-row');
            
            rows.forEach(function(row) {
                let englishTerm = normalizeArabic(row.querySelector('.en-term') ? row.querySelector('.en-term').textContent : '');
                let arabicTerm = normalizeArabic(row.querySelector('.ar-term') ? row.querySelector('.ar-term').textContent : '');
                let definition = normalizeArabic(row.querySelector('.definition-desc') ? row.querySelector('.definition-desc').textContent : '');
                let subject = normalizeArabic(row.querySelector('.subject-field') ? row.querySelector('.subject-field').textContent : '');
                let sourceEn = normalizeArabic(row.querySelector('.source-en') ? row.querySelector('.source-en').textContent : '');
                let sourceAr = normalizeArabic(row.querySelector('.source-ar') ? row.querySelector('.source-ar').textContent : '');
                
                if (englishTerm.includes(filter) || arabicTerm.includes(filter) || definition.includes(filter) || subject.includes(filter) || sourceEn.includes(filter) || sourceAr.includes(filter)) {
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
