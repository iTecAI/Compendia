function condition(c, t, f) { if (c) { return t; } else { return f; } }

function get(url, parameters, success, failure) {
    var success = condition(success, success, console.log);
    var failure = condition(failure, failure, console.log);
    var parameters = condition(parameters, parameters, {});

    if (!localStorage.fingerprint) {
        localStorage.fingerprint = sha256((Date.now()+Math.random()).toString());
    }

    return $.ajax({
        url: url+'?'+$.param(parameters),
        method: 'GET',
        success: success,
        failure: failure,
        headers: {
            'X-Fingerprint': localStorage.fingerprint
        }
    });
}

function post(url, parameters, body, success, failure) {
    var success = condition(success, success, console.log);
    var failure = condition(failure, failure, console.log);
    var parameters = condition(parameters, parameters, {});

    if (!localStorage.fingerprint) {
        localStorage.fingerprint = sha256((Date.now()+Math.random()).toString());
    }

    return $.ajax({
        url: url+'?'+$.param(parameters),
        method: 'POST',
        success: success,
        failure: failure,
        headers: {
            'X-Fingerprint': localStorage.fingerprint
        },
        data: JSON.stringify(body)
    });
}

function root_update(data, force) {
    localStorage.login = data.login;
    localStorage.recent = JSON.stringify(data.recent);

    $('#header .login').text(condition(localStorage.login != 'null' && localStorage, 'Log Out', 'Log In'));

    local_update(data, force);
}

function local_update(data, force) {
    // Override in page-specific files.
}

$(document).ready(function () {
    $('#login-dialog').slideUp(0);
    window.setInterval(function () { get('/api/status', {}, root_update); }, 250);
    $('.login').on('click', function () {
        if (localStorage.login == 'null' || !localStorage.login) {
            if ($('#header .login').hasClass('active')) {
                $('#login-dialog input').val('');
                $('#login-dialog').slideUp(200);
                $('#header .login').animate({
                    'width': '120px'
                }, 200);
                $('#header .login').removeClass('active');
            } else {
                $('#login-dialog input').val('');
                $('#login-dialog').slideDown(200);
                $('#header .login').animate({
                    'width': '200px'
                }, 200);
                $('#header .login').addClass('active');
            }
        } else {
            post('/api/logout');
        }
    });
    $('#login-dialog .finish').on('click', function () {
        var uname = $('#login-dialog .username input').val();
        var passw = $('#login-dialog .password input').val();
        passw = sha256(passw);
        post('/api/login', {}, {
            username: uname,
            hashword: passw
        }).fail(function (result) {
            console.error('Login error '+result.status+' '+result.responseJSON.reason);
            alert('Failed to login: '+result.responseJSON.reason);
        });
        $('.login').trigger('click');
    });
    get('/api/status', {}, function (result) {
        root_update(result, true);
    });
});