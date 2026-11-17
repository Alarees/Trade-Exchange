/** Auto-submit the crop filter on the public exchange board when the
 * crop select changes, so visitors don't need to click "تصفية" twice. */
document.addEventListener("DOMContentLoaded", function () {
    var select = document.querySelector('select[name="crop_id"]');
    if (select) {
        select.addEventListener("change", function () {
            select.closest("form").submit();
        });
    }
});
