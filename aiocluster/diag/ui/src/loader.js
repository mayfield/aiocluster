"use strict";

var aioc = window.aioc || {};
aioc.pages = {
    "about.html": {
        title: 'About',
        icon: 'info',
    },
    "memory.html": {
        title: 'Memory Tracker',
        icon: 'cubes',
    },
    "profiler.html": {
        title: 'Performance Profiler',
        icon: 'clock',
    },
     "ps.html": {
        title: 'Processes',
        icon: 'tasks'
    }
};
   

$(document).ready(function() {
    (async function() {
        const work = [];
        for (const tag of $('script[type="text/x-template"][href]')) {
            work.push($.get(tag.getAttribute('href')).then(v => ({
                tag: $(tag),
                data: v
            })));
        }
        const active_page = window.location.pathname.split('/').pop();
        const context = {
            header: {
                menu: {
                    active: null,
                    inactive: [],
                }
            }
        };
        for (const k of Object.keys(aioc.pages).sort()) {
            if (k == active_page) {
                context.header.menu.active = aioc.pages[k];
            } else {
                const val = aioc.pages[k];
                val.href = k;
                context.header.menu.inactive.push(val);
            }
        }
        for (const x of aioc.util.as_completed(work)) {
            const tpl = await x;
            tpl.tag.after(Handlebars.compile(tpl.data)(context));
        }
    })();
});
