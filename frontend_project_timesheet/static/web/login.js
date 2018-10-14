var redirect = null;

function _barcode_read(value) {
    $.ajax({
        url: '/fetimesheets/login?barcode=' + value,
        type: 'get',
        success: function(data){
            result = $.parseJSON(data);
            if (result.type == 'success') {
                redirect = setTimeout( function() {
                    do_login(result.employee)
                }, 1800 );
                
                alertCardSuccess(result.message)

            } else if (result.type == 'warning') {
                alertCardWarning(result.message)

            } else if (result.type == 'error') {
                alertCardError(result.message)
            }
        },

        error: function() {
        }
    });
}


function listen_barcode(value) {
    if (value.length == 10) {
        _barcode_read(value)
    }
}

function do_login(id) {
    window.location.replace('/fetimesheets/home?eid=' + id)
}


var alertCardTO = false

function alertCardClear() {
    $('.alertcard').removeClass('alert-warning')
    $('.alertcard').removeClass('alert-danger')
    $('.alertcard').removeClass('alert-success')
}

function alertCardSuccess(msg) {
    alertCardClear()
    a = $('.alertcard')
    a.addClass('alert-success')
    a.html(msg)

    if (!alertCardTO) {
        a.animate({opacity: 1}, 300)
    } else {
        clearTimeout(alertCardTO)
    }
        alertCardTO = setTimeout(function () {
                                                a.animate({opacity: 0}, 300);
                                                alertCardTO = false;
                                            }, 2000)
}

function alertCardError(msg) {
    alertCardClear()
    a = $('.alertcard')
    a.addClass('alert-danger')
    a.html(msg)

    if (!alertCardTO) {
        a.animate({opacity: 1}, 300)
    } else {
        clearTimeout(alertCardTO)
    }
        alertCardTO = setTimeout(function () {
                                                a.animate({opacity: 0}, 300);
                                                alertCardTO = false;
                                            }, 2000)
}

function alertCardWarning(msg) {
    alertCardClear()
    a = $('.alertcard')
    a.addClass('alert-warning')
    a.html(msg)

    if (!alertCardTO) {
        a.animate({opacity: 1}, 300)
    } else {
        clearTimeout(alertCardTO)
    }

        alertCardTO = setTimeout(function () {
                                                a.animate({opacity: 0}, 300);
                                                alertCardTO = false;
                                            }, 2000)
}

