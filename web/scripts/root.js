function condition(c, t, f) { if (c) { return t; } else { return f; } }

function get(url, parameters, success, failure) {
    var success = condition(success, success, console.log);
    var failure = condition(failure, failure, console.log);
    var parameters = condition(parameters, parameters, {});

    if (!localStorage.fingerprint) {
        localStorage.fingerprint = sha256((Date.now() + Math.random()).toString());
    }

    return $.ajax({
        url: url + '?' + $.param(parameters),
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
        localStorage.fingerprint = sha256((Date.now() + Math.random()).toString());
    }

    return $.ajax({
        url: url + '?' + $.param(parameters),
        method: 'POST',
        success: success,
        failure: failure,
        headers: {
            'X-Fingerprint': localStorage.fingerprint
        },
        data: JSON.stringify(body)
    });
}

function get_cookies() {
    var str = document.cookie;
    str = str.split(', ');
    var result = {};
    for (var i = 0; i < str.length; i++) {
        var cur = str[i].split('=');
        result[cur[0]] = cur[1];
    }
    return result;
}

function root_update(data, force) {
    localStorage.login = data.login;
    localStorage.recent = JSON.stringify(data.recent);

    $('#header .login').text(condition(localStorage.login != 'null' && localStorage, 'Log Out', 'Log In'));

    try {
        local_update(data, force);
    } catch {

    }
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
            console.error('Login error ' + result.status + ' ' + result.responseJSON.reason);
            alert('Failed to login: ' + result.responseJSON.reason);
        });
        $('.login').trigger('click');
    });
    get('/api/status', {}, function (result) {
        root_update(result, true);
    });
});

function parseParams() {
    var parts = window.location.search.slice(1).split('&');
    var mapping = {};
    for (var p of parts) {
        var _p = p.split('=');
        mapping[_p[0]] = _p[1];
    }
    return mapping;
}

function fallbackCopyTextToClipboard(text) {
    var textArea = document.createElement("textarea");
    textArea.value = text;

    // Avoid scrolling to bottom
    textArea.style.top = "0";
    textArea.style.left = "0";
    textArea.style.position = "fixed";

    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
        var successful = document.execCommand('copy');
        var msg = successful ? 'successful' : 'unsuccessful';
        console.log('Fallback: Copying text command was ' + msg);
    } catch (err) {
        console.error('Fallback: Oops, unable to copy', err);
    }

    document.body.removeChild(textArea);
}
function copyTextToClipboard(text) {
    if (!navigator.clipboard) {
        fallbackCopyTextToClipboard(text);
        return;
    }
    navigator.clipboard.writeText(text).then(function () {
        console.log('Async: Copying to clipboard was successful!');
    }, function (err) {
        console.error('Async: Could not copy text: ', err);
    });
}