var ARTICLE = get_cookies().ARTICLE_ID;

var EDITING = false;
var EDITS = 0;

function update_article(result, force) {
    $('#article-top-bar .title-input').val(result.name);
    $('#article-top-bar .title-input').toggleClass('editable', result.editable);
    $('#article-top-bar .title-input').attr('disabled', !result.editable);
    $('#edit-toggle').toggle(result.editable);

    $("<span class='tag-area'></span>").append(result.tags.map(function (v, i, a) {
        var tag_item = $('<span class="tag-item"></span>').append($('<span class="tag-text"></span>').text(v));
        tag_item.toggleClass('editable', result.editable);
        if (result.editable) {
            tag_item.append(
                $('<button class="delete-tag"></button>')
                    .append('<span class="material-icons">clear</span>')
                    .on('click', function (event) {
                        post('/api/objects/articles/' + ARTICLE + '/tags/delete', {}, { name: $(this).parents('.tag-item').children('.tag-text').text() });
                    })
            );
        }
        return tag_item;
    })).replaceAll('#article-top-bar .tag-area');

    $('.tag-area').on('mousewheel', function (event) {
        $(this).scrollLeft($(this).scrollLeft() + event.originalEvent.deltaY * 0.1);
        event.preventDefault();
    });

    if (EDITING) {
        if (force == true) {
            $('#article-page').html(result.markdown_content.replace(/\n/g, '<br>'));
        }
    } else {
        $('#article-page').html(result.html_content);
    }

    var header_list = $("<div class='headers-area noscroll noselect'></div>");
    for (var header of result.heading_ids) {
        var item = $('<a class="heading-item"></a>')
        item.text(header.text);
        item.attr('data-id', header.id);
        item.css('padding-left', 10 * header.level + 24);
        item.on('click', function (event) {
            var target = $('#'+$(this).attr('data-id'));
            if (target.length) {
                $('#article-page').animate({
                    scrollTop: target.offset().top
                }, 300);
                return false;
            }
        });
        item.append(
            $('<button class="copy-link"></button>')
                .append($('<span class="material-icons">insert_link</span>'))
                .on('click', function () {
                    copyTextToClipboard(location.origin+'/article/'+ARTICLE+'?goto='+$(this).parents('.heading-item').attr('data-id'));
                })
        );

        header_list.append(item);
    }
    header_list.replaceAll('.headers-area');
}

function update_taglist(result) {
    var dummy_list = $("<datalist id='tag-list-select'></datalist>");
    dummy_list.append(result.map(function (v, i, a) {
        return $('<option>').attr('value', v);
    }));
    dummy_list.replaceAll($('#tag-list-select'));
}

function local_update(result, force) {
    if (result.updates.client || result.updates.user || force == true || result.updates.articles[ARTICLE]) {
        get('/api/objects/articles/' + ARTICLE, {}, function (result) {
            update_article(result, force);
        }).fail(function () {
            window.location.pathname = '/';
        });
        get('/api/objects/tags', {}, update_taglist);
        $('#edit-toggle .material-icons').text(condition(EDITING, 'visibility', 'edit'));
    }
    if (EDITING && result.login) {
        $('#article-page').attr('contenteditable', true);
    } else {
        $('#article-page').attr('contenteditable', false);
    }
}

$(document).ready(function () {
    $('#article-top-bar .tag-input').on('change', function () {
        post('/api/objects/articles/' + ARTICLE + '/tags/new', {}, { name: $(this).val() });
        $(this).val('');
    });
    $('#article-top-bar .title-input').on('change', function () {
        post('/api/objects/articles/' + ARTICLE + '/modify/name', {}, { value: $(this).val() });
    });
    $('#edit-toggle').on('click', function () {
        EDITING = !EDITING;
        get('/api/status', {}, function (result) {
            root_update(result, true);
        });
    });
    $('#article-page').on('keydown', function (event) {
        if (EDITING) {
            EDITS += 1;
        }
    });
    window.setInterval(function () {
        if (EDITING && EDITS > 0) {
            EDITS = 0;
            post('/api/objects/articles/' + ARTICLE + '/set_content', {}, { content: $('#article-page')[0].innerText });
        }
    }, 500);

    var params = parseParams();
    if (Object.keys(params).includes('goto')) {
        var target = $('#'+params.goto);
        if (target.length) {
            $('#article-page').animate({
                scrollTop: target.offset().top
            }, 300);
            return false;
        }
    }
});