"use strict";

$(document).ready(function() {
    (async function() {
        const tpl_tag = $('#procs-template');
        const procs_tpl = Handlebars.compile(tpl_tag.html());
        const target_el = tpl_tag.parent();

        while (true) {
            const data = await $.get('/api/v1/ps');
            data.mem_total = data.coordinator.memory.rss;
            data.cpu_total = data.coordinator.cpu_percent;
            for (const x of data.workers) {
                data.mem_total += x.memory.rss;
                data.cpu_total += x.cpu_percent;
            }
            target_el.html(procs_tpl(data));
            await aioc.util.sleep(1);
        }
    })();
});
