var MAP = get_cookies().MAP_ID;

var EDITING = false;
var EDITS = 0;
var TOOL = 'pointer';

var SELECTED_OBJECTS = [];

var scale = 1,
    panning = false,
    xoff = 0,
    yoff = 0,
    start = { x: 0, y: 0 };

var panning_object = null;

var OBJ_ICONS = {
    location: 'place'
};

function setTransform() {
    $('#map-container').css('transform', "translate(" + xoff + "px, " + yoff + "px) scale(" + scale + ")");
}

function getPercentPosition(x, y) {
    return {
        x: (x - $('#map-container').offset().left) / $('#map-container').width() * 100 / scale,
        y: (y - $('#map-container').offset().top) / $('#map-container').height() * 100 / scale
    }
}

function update_objects(objects) {
    var dummy_objects = $("<div id='object-container'></div>");
    for (var object of Object.values(objects)) {
        console.log(object);
        var item = $('<div class="map-object"></div>');
        item.attr('data-type', object.type);
        item.attr('data-id', object.id);
        if (SELECTED_OBJECTS.includes(object.id)) {
            item.addClass('selected');
        }
        item.css({
            top: object.position.y+'%',
            left: object.position.x+'%'
        });
        item.append($('<span class="material-icons object-icon noselect"></span>').text(OBJ_ICONS[object.type]));

        if (object.type == 'location') {
            var loc_menu = $('<div class="object-content loc-menu shadow noselect"></div>');
            loc_menu.append(
                $('<input class="loc-name-input" placeholder="Location Name">')
                    .attr('disabled', !(EDITING && localStorage.login != 'null'))
                    .val(object.name)
                    .on('change', function (event) {
                        post('/api/objects/maps/' + MAP + '/modify/' + [
                            'objects',
                            $(event.delegateTarget).parents('.map-object').attr('data-id'),
                            'name'
                        ].join('.'), {}, {
                            value: $(this).val()
                        });
                    })
            );
            if (localStorage.login != 'null' && EDITING) {
                loc_menu.append(
                    $('<button class="menu-btn visibility"></button>')
                        .append(
                            $('<span class="material-icons"></span>')
                                .text(condition(object.public, 'visibility_off', 'visibility'))
                        )
                        .on('click', function (event) {
                            post('/api/objects/maps/' + MAP + '/modify/' + [
                                'objects',
                                $(event.delegateTarget).parents('.map-object').attr('data-id'),
                                'public'
                            ].join('.'), {}, {
                                value: $(this).children('.material-icons').text() == 'visibility'
                            });
                        })
                );
                loc_menu.append(
                    $('<button class="menu-btn delete"></button>')
                        .append(
                            $('<span class="material-icons">delete</span>')
                        )
                        .on('click', function (event) {
                            post('/api/objects/maps/' + MAP + '/objects/' + $(event.delegateTarget).parents('.map-object').attr('data-id') + '/delete');
                        })
                );
            }
            loc_menu.append('<span class="material-icons link-icon">link</span>');
            loc_menu.append(
                $('<div class="loc-link-input-wrapper"></div>')
                    .append(
                        $('<input class="loc-link-input" placeholder="Article Link">')
                            .attr('disabled', !(EDITING && localStorage.login != 'null'))
                            .val(object.link)
                            .on('change', function (event) {
                                post('/api/objects/maps/' + MAP + '/modify/' + [
                                    'objects',
                                    $(event.delegateTarget).parents('.map-object').attr('data-id'),
                                    'link'
                                ].join('.'), {}, {
                                    value: $(this).val()
                                });
                            })
                    )
                    .on('click', function (event) {
                        if (!EDITING) {
                            window.open($(this).children('input').val());
                        }
                    })
            );
            loc_menu.append(
                $('<textarea class="loc-desc-input" placeholder="Location Description" resizeable="no"></textarea>')
                    .attr('disabled', !(EDITING && localStorage.login != 'null'))
                    .val(object.description)
                    .on('change', function (event) {
                        post('/api/objects/maps/' + MAP + '/modify/' + [
                            'objects',
                            $(event.delegateTarget).parents('.map-object').attr('data-id'),
                            'description'
                        ].join('.'), {}, {
                            value: $(this).val()
                        });
                    })
            );
            
            item.append(loc_menu);
        }

        item.on('click', function (event) {
            if (!target_member_of(event.target, ['.object-icon'])) {
                return;
            }
            if (EDITING && TOOL == 'move') {
                return;
            }
            if ($(this).hasClass('selected')) {
                $(this).removeClass('selected');
                SELECTED_OBJECTS.splice(SELECTED_OBJECTS.indexOf($(this).attr('data-id')));
            } else {
                $(this).addClass('selected');
                SELECTED_OBJECTS.push($(this).attr('data-id'));
            }
        });

        dummy_objects.append(item);
    }
    dummy_objects.replaceAll('#object-container');
}

function update_map(result, force) {
    $('#map-top-bar .title-input').val(result.name);
    $('#map-top-bar .title-input').toggleClass('editable', result.editable);
    $('#map-top-bar .title-input').attr('disabled', !result.editable);
    $('#edit-toggle').toggle(result.editable);

    $("<span class='tag-area'></span>").append(result.tags.map(function (v, i, a) {
        var tag_item = $('<span class="tag-item"></span>').append($('<span class="tag-text"></span>').text(v));
        tag_item.toggleClass('editable', result.editable);
        if (result.editable) {
            tag_item.append(
                $('<button class="delete-tag"></button>')
                    .append('<span class="material-icons">clear</span>')
                    .on('click', function (event) {
                        post('/api/objects/maps/' + MAP + '/tags/delete', {}, { name: $(this).parents('.tag-item').children('.tag-text').text() });
                    })
            );
        }
        return tag_item;
    })).replaceAll('#map-top-bar .tag-area');

    $('.tag-area').on('mousewheel', function (event) {
        $(this).scrollLeft($(this).scrollLeft() + event.originalEvent.deltaY * 0.1);
        event.preventDefault();
    });
    $('#main-map').attr('src', result.map_data.replace('$', window.location.origin));
    update_objects(result.objects);
}

function update_taglist(result) {
    var dummy_list = $("<datalist id='tag-list-select'></datalist>");
    dummy_list.append(result.map(function (v, i, a) {
        return $('<option>').attr('value', v);
    }));
    dummy_list.replaceAll($('#tag-list-select'));
}

function local_update(result, force) {
    $('#toolbar button').not('[data-tool=' + TOOL + ']').removeClass('selected');
    $('#toolbar button[data-tool=' + TOOL + ']').addClass('selected');
    $('body').attr('data-tool', condition(EDITING && result.login, TOOL, 'move'));
    if (EDITING && result.login) {
        $('#toolbar').show();
    } else {
        $('#toolbar').hide();
    }
    if (result.updates.client || result.updates.user || force == true || result.updates.maps[MAP]) {
        get('/api/objects/maps/' + MAP, {}, function (result) {
            update_map(result, force);
        }).fail(function () {
            window.location.pathname = '/';
        });
        get('/api/objects/tags', {}, update_taglist);
        $('#edit-toggle .material-icons').text(condition(EDITING, 'visibility', 'edit'));
    }
}

$(document).ready(function () {
    $('#map-top-bar .tag-input').on('change', function () {
        post('/api/objects/maps/' + MAP + '/tags/new', {}, { name: $(this).val() });
        $(this).val('');
    });
    $('#map-top-bar .title-input').on('change', function () {
        post('/api/objects/maps/' + MAP + '/modify/name', {}, { value: $(this).val() });
    });
    $('#edit-toggle').on('click', function () {
        EDITING = !EDITING;
        get('/api/status', {}, function (result) {
            root_update(result, true);
        });
    });
    $('#map-page').on('keydown', function (event) {
        if (EDITING) {
            EDITS += 1;
        }
    });

    var params = parseParams();
    if (Object.keys(params).includes('goto')) {
        var target = $('#' + params.goto);
        if (target.length) {
            $('#map-page').animate({
                scrollTop: target.offset().top
            }, 300);
            return false;
        }
    }

    // Map zoom/pan
    $('#map-container').on('mousedown', function (e) {
        if (target_member_of(e.target, [
            '.map-object[data-type=location]'
        ])) {
            if (EDITING && TOOL == 'move' && localStorage.login != 'null') {
                if ($(e.target).is('.map-object[data-type=location]')) {
                    var el = $(e.target);
                } else {
                    var el = $($(e.target).parents('.map-object[data-type=location]').toArray()[0]);
                }
                panning_object = $(el);
            }
            return;
        }
        if (!EDITING || (EDITING && TOOL == 'move')) {
            e.preventDefault();
            start = { x: e.clientX - xoff, y: e.clientY - yoff };
            panning = true;
        }
    });

    $('#map-container').on('mouseup', function (e) {
        panning = false;
        if (panning_object != null) {
            post('/api/objects/maps/' + MAP + '/modify/' + [
                'objects',
                panning_object.attr('data-id'),
                'position'
            ].join('.'), {}, {
                value: getPercentPosition(e.clientX, e.clientY)
            });
            panning_object = null;
        }
    });

    $('#map-container').on('mousemove', function (e) {
        e.preventDefault();
        if (panning_object != null) {
            var pos = getPercentPosition(e.clientX, e.clientY);
            $(panning_object).css({
                top: pos.y+'%',
                left: pos.x+'%'
            });
            return;
        }
        if (!panning) {
            return;
        }
        xoff = (e.clientX - start.x);
        yoff = (e.clientY - start.y);
        setTransform();
    });

    $('#map-container').on('wheel', function (e) {
        e.preventDefault();
        e = e.originalEvent;
        // take the scale into account with the offset
        var xs = (e.clientX - xoff) / scale,
            ys = (e.clientY - yoff) / scale,
            delta = (e.wheelDelta ? e.wheelDelta : -e.deltaY);

        // get scroll direction & set zoom level
        (delta > 0) ? (scale *= 1.2) : (scale /= 1.2);

        // reverse the offset amount with the new scale
        xoff = e.clientX - xs * scale;
        yoff = e.clientY - ys * scale;

        setTransform();
    });
    $('#toolbar button').on('click', function () {
        TOOL = $(this).attr('data-tool');
        $('#toolbar button').not('[data-tool=' + TOOL + ']').removeClass('selected');
        $('#toolbar button[data-tool=' + TOOL + ']').addClass('selected');
    });

    // Tool functions
    $('#map-container').on('click', function (event) {
        event.preventDefault();
        if (EDITING && localStorage.login != 'null') {
            $('#map-container').trigger('evt_' + TOOL, [
                getPercentPosition(event.clientX, event.clientY),
                event.target
            ]);
        }
    });
    $('#map-container').on('evt_location', function (event, pos, target) {
        console.log(event, pos, target);
        var loc_name = prompt('Enter location name.');
        if (loc_name) {
            var oid = sha256((Date.now() + Math.random()).toString());
            post('/api/objects/maps/' + MAP + '/modify/' + [
                'objects',
                oid
            ].join('.'), {}, {
                value: {
                    id: oid,
                    name: loc_name,
                    link: null,
                    type: 'location',
                    public: true,
                    description: '',
                    position: pos
            }
            });
        }
    });
});