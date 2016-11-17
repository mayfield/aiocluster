"use strict";

$(document).ready(function() {
    (async function() {
        const tpl_tag = $('#procs-template');
        const procs_tpl = Handlebars.compile(tpl_tag.html());
        const target_el = tpl_tag.parent();

        target_el.html(procs_tpl(await $.get('/api/v1/about')));
        $('.ui.accordion').accordion();
    })();
});
