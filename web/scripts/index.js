var OBJECT_TYPES = {
    article: 'description',
    map: 'map'
};

function render_recents() {
    var recents = JSON.parse(localStorage.recent);
    if (recents.length == 0) {
        $('#recent-container').html('<span class="no-recents noselect">No Recent Objects</span>');
    } else {

    }
}

function render_objects(result) {
    console.log(result);
    var dummy_obj_area = $("<div id='object-area' class='noscroll noselect'></div>");
    for (var object of result) {
        if (
            (
                object.name.toLowerCase().includes($('input.search-query').val().toLowerCase()) || 
                $('input.search-query').val().toLowerCase().includes(object.name.toLowerCase()) ||
                $('input.search-query').val() == ''
            ) && (
                object.tags.includes($('select.search-tag-select').val()) || 
                $('select.search-tag-select').val() == '$no-tags'
            )
        ) {
            var object_item = $('<div class="object-item"></div>');
            object_item.attr('data-id', object.id);
            object_item.append(
                $('<img class="thumbnail shadow">').attr('src', condition(object.thumbnail, object.thumbnail, '/s/assets/article_default.png'))
            );
            object_item.append(
                $('<div class="description"></div>')
                    .append(
                        $('<span class="material-icons object-type-icon"></span>').text(OBJECT_TYPES[object.type])
                    )
                    .append(
                        $('<span class="object-name"></span>').text(object.name)
                    )
                    .append('<span class="tag-icon material-icons">local_offer</span>')
                    .append(
                        $('<span class="tag-list noscroll"></span>')
                            .append(object.tags.map(function (v, i, a) {
                                return $('<span class="tag-item"></span>').text(v);
                            }))
                            .on('mousewheel', function (event) {
                                $(this).scrollLeft($(this).scrollLeft() + event.originalEvent.deltaY * 0.1);
                                event.preventDefault();
                            })
                    )
            );
            if (object.can_edit) {
                object_item.append(
                    $('<button class="edit-obj-button set-visibility shadow"></button>')
                        .append($('<span class="material-icons"></span>').text(condition(object.public, 'visibility', 'visibility_off')))
                        .toggleClass('public', object.public == true)
                        .on('click', function (event) {
                            post('/api/objects/articles/'+$(this).parents('.object-item').attr('data-id')+'/modify/public', {}, {value: !$(this).hasClass('public')});
                        })
                );
                object_item.append(
                    $('<button class="edit-obj-button delete shadow"></button>')
                        .append($('<span class="material-icons">delete</span>'))
                        .on('click', function (event) {
                            post('/api/objects/articles/'+$(this).parents('.object-item').attr('data-id')+'/delete');
                        })
                );
            }
            object_item.on('click', function (event) {
                if (!$(event.target).hasClass('edit-obj-button') && $(event.target).parents('.edit-obj-button').length == 0) {
                    window.open('/article/'+$(this).attr('data-id'), '_blank');
                }
            });

            dummy_obj_area.append(object_item);
        }
    }
    dummy_obj_area.replaceAll('#object-area');
}

function reload_tags(result) {
    var curval = $('select.search-tag-select').val();
    var dummy_select = $('<select name="tags" class="search-tag-select"></select>');
    dummy_select.append('<option value="$no-tags">No Filter</option>');
    dummy_select.append(result.map(function (v, i, a) { return $('<option></option>').attr('value', v).text(v); }));
    dummy_select.replaceAll('select.search-tag-select');
    if (result.includes(curval)) {
        $('select.search-tag-select').val(curval);
    } else {
        $('select.search-tag-select').val('$no-tags');
    }
}

function local_update(result, force) {
    if (result.login) {
        $('#new-obj-button').show();
    } else {
        $('#new-obj-button').hide();
    }
    if (result.updates.client || result.updates.user || force == true || Object.values(result.updates.articles).some(function (v, i, a) {return v;})) {
        render_recents();
        get('/api/objects/', {}, render_objects);
        get('/api/objects/tags', {}, reload_tags);
    }
}

$(document).ready(function () {
    $('.obj-button.article').on('click', function () {
        post('/api/objects/articles/new');
    });
    $('input.search-query').on('change', function () {
        get('/api/status', {}, function (result) {
            root_update(result, true);
        });
    });
    $('select.search-tag-select').on('change', function () {
        get('/api/status', {}, function (result) {
            root_update(result, true);
        });
    });
});