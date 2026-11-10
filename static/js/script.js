// دوال مساعدة للهروب والتظليل الآمن
function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// دالة بناء التعبير النمطي (RegExp) لدعم تطبيع الأحرف والتشكيل العربي والأحرف الإنجليزية
function buildHighlightRegex(query) {
    if (!query) return null;
    const cleanQuery = query.replace(/[\u064B-\u0652\u0670]/g, '').trim();
    if (!cleanQuery) return null;

    const tashkeel = '[\\u064B-\\u0652\\u0670]*';
    let pattern = '';

    for (let i = 0; i < cleanQuery.length; i++) {
        const ch = cleanQuery[i];
        if (/[أإآا]/.test(ch)) {
            pattern += '[أإآا]' + tashkeel;
        } else if (/[يى]/.test(ch)) {
            pattern += '[يى]' + tashkeel;
        } else if (/[ةه]/.test(ch)) {
            pattern += '[ةه]' + tashkeel;
        } else if (/[.*+?^${}()|[\]\\]/.test(ch)) {
            pattern += '\\' + ch;
        } else if (/\s/.test(ch)) {
            pattern += '\\s+';
        } else {
            pattern += ch.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + tashkeel;
        }
    }

    try {
        return new RegExp('(' + pattern + ')', 'gi');
    } catch (e) {
        return null;
    }
}

// تطبيق التظليل الأصفر مع الحفاظ على النص الأصلي ومنع ثغرات XSS
function applyHighlight(cell, regex) {
    if (!cell) return false;

    // حفظ النص الأصلي أول مرة فقط
    if (!cell.hasAttribute('data-original-text')) {
        cell.setAttribute('data-original-text', cell.textContent);
    }

    const rawText = cell.getAttribute('data-original-text');
    if (!rawText || rawText.trim() === '' || rawText.trim() === '-') {
        cell.textContent = rawText;
        return false;
    }

    if (!regex) {
        cell.textContent = rawText;
        return false;
    }

    regex.lastIndex = 0;
    let match = regex.exec(rawText);
    if (!match) {
        cell.textContent = rawText;
        return false;
    }

    // بناء النص المظلل مع تعقيم كافة المحارف
    let result = '';
    let lastIndex = 0;
    regex.lastIndex = 0;

    while ((match = regex.exec(rawText)) !== null) {
        const before = rawText.substring(lastIndex, match.index);
        result += escapeHtml(before);
        result += '<mark class="search-highlight">' + escapeHtml(match[0]) + '</mark>';
        lastIndex = match.index + match[0].length;

        if (match[0].length === 0) {
            regex.lastIndex++;
        }
    }

    result += escapeHtml(rawText.substring(lastIndex));
    cell.innerHTML = result;
    return true;
}

document.addEventListener('DOMContentLoaded', function() {
    // إخفاء الإشعارات بعد 4 ثوانٍ
    setTimeout(function() {
        let alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            if (typeof bootstrap !== 'undefined') {
                let bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } else {
                alert.style.display = 'none';
            }
        });
    }, 4000);

    // البحث في القاموس: محصور فقط في عمود المصطلح الإنجليزي والمقابل العربي مع التظليل الأصفر
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = searchInput.value.trim();
            const regex = buildHighlightRegex(query);
            const rows = document.querySelectorAll('.term-row');

            rows.forEach(function(row) {
                const enCell = row.querySelector('.en-term');
                const arCell = row.querySelector('.ar-term');

                if (!query) {
                    applyHighlight(enCell, null);
                    applyHighlight(arCell, null);
                    row.style.display = "";
                    return;
                }

                // الفحص والتظليل في عمودي (المصطلح الإنجليزي) و (المقابل العربي) فقط
                const enMatch = applyHighlight(enCell, regex);
                const arMatch = applyHighlight(arCell, regex);

                if (enMatch || arMatch) {
                    row.style.display = "";
                } else {
                    row.style.display = "none";
                }
            });
        });
    }

    // دعم نفس منطق البحث والتظليل الأصفر في جدول المصطلحات المعتمدة بلوحة الأدمن
    const approvedSearch = document.getElementById('approvedSearch');
    if (approvedSearch) {
        approvedSearch.addEventListener('input', function() {
            const query = approvedSearch.value.trim();
            const regex = buildHighlightRegex(query);
            const rows = document.querySelectorAll('#approvedTable .approved-row');

            rows.forEach(function(row) {
                const enCell = row.querySelector('.approved-english');
                const arCell = row.querySelector('.approved-arabic');

                if (!query) {
                    applyHighlight(enCell, null);
                    applyHighlight(arCell, null);
                    row.style.display = "";
                    return;
                }

                const enMatch = applyHighlight(enCell, regex);
                const arMatch = applyHighlight(arCell, regex);

                if (enMatch || arMatch) {
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
