document.addEventListener('DOMContentLoaded', function() {
    // إخفاء الإشعارات بعد 4 ثوانٍ
    setTimeout(function() {
        let alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            // التأكد من وجود بوتستراب لتفادي أخطاء الكونسول
            if(typeof bootstrap !== 'undefined') {
                let bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } else {
                alert.style.display = 'none';
            }
        });
    }, 4000);

    // البحث المباشر في صفحة القاموس (محدث ليعمل مع الجداول)
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            let filter = searchInput.value.toLowerCase();
            // جلب جميع صفوف الجدول (<tr>)
            let rows = document.querySelectorAll('.term-row');
            
            rows.forEach(function(row) {
                // جلب النصوص من كل عمود (<td>) داخل الصف
                let englishTerm = row.querySelector('.english-term').textContent.toLowerCase();
                let arabicTerm = row.querySelector('.arabic-term').textContent.toLowerCase();
                let arabicDesc = row.querySelector('.arabic-desc').textContent.toLowerCase();
                
                // إظهار الصف إذا كان أي من الأعمدة يحتوي على نص البحث
                if (englishTerm.includes(filter) || arabicTerm.includes(filter) || arabicDesc.includes(filter)) {
                    row.style.display = ""; 
                } else {
                    row.style.display = "none"; // إخفاء الصف إذا لم يطابق
                }
            });
        });
    }
});
// تفعيل خاصية تحديد الكل (Select All) في جدول الأدمن
    const selectAllCheckbox = document.getElementById('selectAll');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            // جلب جميع مربعات التحديد الخاصة بالمصطلحات
            const checkboxes = document.querySelectorAll('.term-checkbox');
            // جعل حالة كل مربع مطابقة لحالة مربع (تحديد الكل)
            checkboxes.forEach(cb => cb.checked = selectAllCheckbox.checked);
        });
    }
// رسالة تأكيد للأدمن
function confirmAction(message) {
    return confirm(message);
}