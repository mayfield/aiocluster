"use strict";



$(document).ready(function() {
    (async function() {
        const workers = new Map();

        $(document).on('click', '.kill', function() {
            const worker = workers.get(Number(this.getAttribute('worker_ident')));
            aioc.tpl.render('#kill-template', worker);
            $('#kill-dialog').modal({
                onApprove: () => aioc.api.request('KILL', 'ps', worker.ident)
            }).modal('show');
        });

        while (true) {
            const data = await aioc.api.get('ps');
            workers.clear();
            data.coordinator.cpu_time = data.coordinator.cpu_times.user +
                                        data.coordinator.cpu_times.system;
            data.cpu_time = data.coordinator.cpu_time;
            data.mem_total = data.coordinator.memory.rss;
            data.cpu_total = data.coordinator.cpu_percent;
            data.open_files_total = data.coordinator.open_files;
            for (const x of data.workers) {
                workers.set(x.ident, x);
                x.cpu_time = x.cpu_times.user + x.cpu_times.system;
                data.cpu_time += x.cpu_time;
                data.mem_total += x.memory.rss;
                data.cpu_total += x.cpu_percent;
                data.open_files_total += x.open_files;
            }
            aioc.tpl.render('#stats-template', data);
            aioc.tpl.render('#procs-template', data, 'tbody');

            await aioc.util.sleep(1);
        }
    })();
});
