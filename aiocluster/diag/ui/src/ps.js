"use strict";

function kill_worker(ident) {
    if (!confirm("Please confirm kill of worker: " + ident))
        return;
    aioc.api.request('KILL', 'ps', ident);
}

$(document).ready(function() {
    (async function() {
        const stats_tpl = Handlebars.compile($('#stats-template').html());
        const procs_tpl = Handlebars.compile($('#procs-template').html());
        const stats_holder = $('#stats-holder');
        const procs_holder = $('#procs-holder');

        while (true) {
            const data = await aioc.api.get('ps');
            data.mem_total = data.coordinator.memory.rss;
            data.cpu_total = data.coordinator.cpu_percent;
            data.open_files_total = data.coordinator.open_files;
            for (const x of data.workers) {
                data.mem_total += x.memory.rss;
                data.cpu_total += x.cpu_percent;
                data.open_files_total += x.open_files;
            }
            stats_holder.html(stats_tpl(data));
            procs_holder.html(procs_tpl(data));
            await aioc.util.sleep(1);
        }
    })();
});
