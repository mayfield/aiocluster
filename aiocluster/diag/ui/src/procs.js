"use strict";

$(document).ready(function() {
    (async function() {
        const tpl_tag = $('#procs-template');
        const procs_tpl = Handlebars.compile(tpl_tag.html());
        const target_el = tpl_tag.parent();

        var myLineChart = new Chartist.Line('#cpu-graph');

        while (true) {
            let mem_sum = 0;
            let cpu_sum = 0;
            const api_data = await $.get('/api/v1/ps');
            
            api_data.workers.forEach(function(x) {
                mem_sum += x.memory.rss;
                cpu_sum += x.cpu_percent;
            });
            target_el.html(procs_tpl(api_data));
            $('#worker-count').html(api_data.workers.length);
            $('#mem-usage').html(aioc.conv.megabytes(mem_sum));
            $('#cpu-usage').html(aioc.conv.percent(cpu_sum));
            await aioc.util.sleep(1);
        }
    })();
});
