"use strict";

$(document).ready(function() {
    (async function() {
        aioc.tpl.render('#about-template', await aioc.api.get('about'));
        $('.ui.accordion').accordion();
    })();
});
