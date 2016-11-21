"use strict";

$(document).ready(function() {
    (async function() {
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
            aioc.tpl.render('#mem-template', {type: totals});
            await aioc.util.sleep(5);
        }
    })();
});
