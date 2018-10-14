$(document).ready(function() {
    var clock_start = setInterval(function() {
                                                $(".web_kiosk_clock").text(new Date().toLocaleTimeString('it-IT', {hour: '2-digit', minute:'2-digit'}));
                                                $("#barcode_reader").focus();
                                              }, 500);
    $(".web_kiosk_clock").text(new Date().toLocaleTimeString('it-IT', {hour: '2-digit', minute:'2-digit'}));
    
    var reloadTimeout = setTimeout( page_reload, 60000 );
});

var inTimeout;
var deferredLoginTimeout;
var stocked_tmb = '';
var delayer = null

function _barcode_read(value) {
    $("#barcode_reader").val('')
    reset_to_read()
    if (Boolean(value) & !delayer) {
        $.ajax({
            url: '/hr/kiosk/login?barcode=' + value + '&time=' + (new Date()).toISOString(),
            type: 'get',
            success: function(data){
                result = $.parseJSON(data);
                delayer = setTimeout( function () { delayer = null } , 1000 );
                if (result.result == 'success') {
                        show_login(result);
                } else if (result.result == 'error') {
                        show_error(result);
                }
            },
            error: function() {
                show_deferred_login(value);
                stocked_tmb = stocked_tmb+'*'+(new Date()).toISOString()+'@'+value;
                deferredLoginTimeout = setTimeout( do_deferred_login, 3000 );
            }
        });
    }
}

function listen_barcode(value) {
    clearTimeout(inTimeout);
    inTimeout = setTimeout( function() {_barcode_read(value)}, 300 );
}

function show_deferred_login(barcode) {
    $('#d_employee_barcode').text(barcode)

    $('#d_check_time').text(new Date().toLocaleTimeString('it-IT', {hour: '2-digit', minute:'2-digit'}))

    $('.web_kiosk_waiting').addClass('hidden')
    $('.web_kiosk_loggedin_offline').removeClass('hidden')

    setTimeout(reset_to_read, 5000)
}

function show_login(data) {
    console.log('ok');
    $('#employee_name').text(data.employee_name);

    if(data.in) {
        $('#check_type').text('entrando');
    } else {
        $('#check_type').text('uscendo');
    }

    if(data.cta){
        $('.web_kiosk_calltoaction').removeClass('hidden');
    }

    $('#check_time').text(new Date().toLocaleTimeString('it-IT', {hour: '2-digit', minute:'2-digit'}));
    $('#employee_image').attr('src', data.employee_image_url);

    $('.web_kiosk_waiting').addClass('hidden');
    $('.web_kiosk_loggedin').removeClass('hidden');

    setTimeout(reset_to_read, 5000);
}

function show_error(data) {
    
    $('#errorbox').text(data.error_text)
    $('#errorbox').removeClass('hidden')
    $('.web_kiosk_waiting').addClass('hidden');
    setTimeout( function() { $('#errorbox').addClass('hidden'); $('.web_kiosk_waiting').removeClass('hidden'); } , 3000)
}

function reset_to_read() {
    $('.web_kiosk_waiting').removeClass('hidden')
    $('.web_kiosk_loggedin').addClass('hidden')
    $('.web_kiosk_loggedin_offline').addClass('hidden')
    $('.web_kiosk_calltoaction').addClass('hidden');
}

function page_reload() {
    $.ajax({
        url: '/service/ping',
        type: 'get',
        success: function() {
            if (stocked_tmb) {
                $.ajax({
                    url: '/hr/kiosk/deferred_login?tmbs=' + stocked_tmb,
                    type: 'get',
                    success: function(data){
                        location.reload();
                    },
                    error: function() {
                        reloadTimeout = setTimeout( page_reload, 10000 );
                    }
                });
            } else {
                location.reload();
            }
        },
        error: function() {
            reloadTimeout = setTimeout( page_reload, 10000 );
        }
    });
}

function do_deferred_login() {
    $.ajax({
        url: '/hr/kiosk/deferred_login?tmbs=' + stocked_tmb,
        type: 'get',
        success: function(data){
            stocked_tmb = ""
        },
        error: function() {
            deferredLoginTimeout = setTimeout( do_deferred_login, 3000 );
        }
    });
}