function showFlash(message,category){
    $('#js-' + category + '-alert').html(message);
    $('#js-' + category + '-alert').delay(500).fadeIn('normal',function(){
        $(this).delay(2500).fadeOut();
    });
}
