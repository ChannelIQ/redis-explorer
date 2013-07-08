$(document).ready(function() {
    // Ensure that all boxes are check on page load
    $('.filterCheckbox').each(function() {
        $(this).prop('checked', true);
    });

    $('#loadingImage').hide();

    // Hide or unhide results rows
    $('.filterCheckbox').change(function() {
        var type = $(this).val();
        var checked = $(this).prop('checked');
        //$('#loadingImage').show();
        $('.keySearchMatch').each(function() {
            if ($(this).children('td').eq(2).text() == type) {
                if (checked) {
                    $(this).show();
                } else {
                    $(this).hide();
                }

                // Uncheck to avoid accidental deletes
                $(this).find(':checkbox').attr("checked", false);
            }
        });
        $('#loadingImage').hide();
    });
});
