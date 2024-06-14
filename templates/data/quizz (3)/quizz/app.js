const loadingTimeout = setTimeout(closeLoading, 1000);

function closeLoading() {
    $('.loading').remove();
    clearTimeout(loadingTimeout);
}

$(document).on('click', '#toggleMobileTool', function () {
    if ($(this).find('span').hasClass('fa-plus')) {
        $('#toggleMobileTool span').addClass('fa-minus');
        $('#toggleMobileTool span').removeClass('fa-plus');
        $('.list-optionBtn-mobile').css('display', 'flex');
        $('.chatBox .chatMeassge').css('height', 'calc(100% - 190px)');

    } else {
        $('#toggleMobileTool span').addClass('fa-plus');
        $('#toggleMobileTool span').removeClass('fa-minus');
        $('.list-optionBtn-mobile').css('display', 'none');
        $('.chatBox .chatMeassge').css('height', 'calc(100% - 120px)');

    }
});
