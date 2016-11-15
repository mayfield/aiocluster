"use strict";

$(document).ready(function() {
    (async function() {
        const work = $('script[type="text/x-autotemplate"]').map(function(i, tag) {
            return $.get(tag.getAttribute('url')).then(function(v) {
                return {
                    tag: $(tag),
                    data: v
                };
            });
        });
        for (const x of aioc.util.as_completed(work)) {
            const tpl = await x;
            tpl.tag.after(Handlebars.compile(tpl.data)({}));
        }
    })();
});
