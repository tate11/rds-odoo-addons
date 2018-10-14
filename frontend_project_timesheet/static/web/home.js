var focused_el = null

$(document).mouseup(function(e) {
    if (!focused_el)
        return

    if (!focused_el.is(e.target) && focused_el.has(e.target).length === 0) {
        focused_el.animate({height: '7vw'}, 600)
    }
});

function addFocus(el) {
    focused_el = $(el)
    focused_el.animate({height: '60vh'}, 600)
}


function setStatus(el, status) {
    el.removeClass('status_working status_blocked status_done status_normal')
    el.addClass('status_'+status)
    el.attr('data-status', status)
}

function close(el){
    el.css('overflow', 'hidden')
    el.animate({opacity: 0, height: '0px'}, 1000, function(){el.remove()})
}

function done(el) {
    el = $(el)
    taskel = el.parents(".task")

    task = taskel.attr('data-id')
    status = taskel.attr('data-status')

    if (status == 'blocked') {
        alertCardError("Non è possibile completare su una operazione bloccata.")
        return
    }

    $.ajax({
        url: '/fetimesheets/done/?task_id=' + task,
        type: 'get',
        success: function(data) {
            result = $.parseJSON(data);
            if ((result.type == 'success') || (result.type == 'warning') ) { 
                
                startclock = el.siblings('.taskinfo').find('.taskvalue.startclock')
                
                setStatus(taskel, 'done')
                startclock.html('')
                close(taskel)
                alertCardSuccess(result.message)
            } else {
                alertCardError(result.message)
            }
        },
        error: function() {
        }
    }); 
}

function block(el) {
    el = $(el)
    taskel = el.parents(".task")

    task = taskel.attr('data-id')
    status = taskel.attr('data-status')

    if (status == 'blocked') {
        return
    }

    $.ajax({
        url: '/fetimesheets/block/?task_id=' + task,
        type: 'get',
        success: function(data) {
            result = $.parseJSON(data);
            if ((result.type == 'success') || (result.type == 'warning') ) { 
                
                startclock = el.siblings('.taskinfo').find('.taskvalue.startclock')

                el.removeClass('fa-pause')
                el.addClass('fa-play')
                
                setStatus(taskel, 'blocked')
                startclock.html('')
                
            }
            
            alertCardError(result.message)
        },
        error: function() {
        }
    }); 
}

function startWork(el) {
    el = $(el)
    taskel = el.parents(".task")

    task = taskel.attr('data-id')
    status = taskel.attr('data-status')

    if (status == 'blocked') {
        alertCardError("Non è possibile lavorare su una operazione bloccata.")
        return
    }

    $.ajax({
        url: '/fetimesheets/start/?task_id=' + task,
        type: 'get',
        success: function(data){
            result = $.parseJSON(data);
            if ((result.type == 'success') || (result.type == 'warning') ) { 
                
                startclock = el.siblings('.taskinfo').find('.taskvalue.startclock')

                if (result.datetime == false) {
                    el.removeClass('fa-pause')
                    el.addClass('fa-play')
                    startclock.html('')

                    setStatus(taskel, 'normal')

                } else {
                    el.removeClass('fa-play')
                    el.addClass('fa-pause')

                    startclock.html(result.datetime)
                    setStatus(taskel, 'working')
                }

                if (result.type == 'success')
                    alertCardSuccess(result.message)
                if (result.type == 'warning')
                    alertCardWarning(result.message)
                
            } else {
                alertCardError(result.message)
            }
        },
        error: function() {
        }
    });
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


function quit() {
    window.location.replace('/fetimesheets')
}