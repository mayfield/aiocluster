
$(document).ready(function() {
    (async function() {
        const mem_tpl = Handlebars.compile($('#mem-template').html());
        const mem_holder = $('#mem-holder');

        while (true) {
            let totals = new Map();
            const data = await aioc.api.get('memory');
            for (const worker of data) {
                for (const [type, count] of worker) {
                    totals.set(type, (totals.get(type) || 0) + count);
                }
            }
            totals = Array.from(totals.entries());
            totals.sort((a, b) => a[1] < b[1] ? 1 : -1);
            mem_holder.html(mem_tpl({type: totals}));
            await aioc.util.sleep(2);
        }
    })();
});
