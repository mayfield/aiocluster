"use strict";

$(document).ready(function() {
    (async function() {
        let prev_totals = {};
        let prev_ts = null;

        await aioc.api.put('profiler/active', true);
        while (true) {
            const limit = 10; // XXX Pull from UI.
            const sortkey = 'inlinetime'; // XXX pull from ui.
            const report = await aioc.api.get('profiler/report');
            const ts = (new Date()).getTime();
            const totals = {};

            for (const batch of report) {
                for (const x of batch) {
                    let key = [
                        x.call.file,
                        x.call.function,
                        x.call.lineno
                    ].join(':');
                    if (totals[key] === undefined) {
                        x.stats.call = key;
                        totals[key] = x.stats;
                    } else {
                        let ref = totals[key];
                        ref.totaltime += x['stats']['totaltime'];
                        ref.inlinetime += x['stats']['inlinetime'];
                        ref.callcount += x['stats']['callcount'];
                    }
                }
            }

            if (prev_ts === null) {
                prev_ts = ts;
                prev_totals = totals;
                await aioc.util.sleep(0.100);  // Get something up quick.
                continue;
            }

            let period = (ts - prev_ts) / 1000;
            for (const call of Object.keys(totals)) {
                let stats = totals[call];
                if (prev_totals[call] !== undefined) {
                    const prev = prev_totals[call];
                    const sample_total = Math.max(stats.inlinetime -
                                                  prev.inlinetime, 0);
                    const sample_calls = stats.callcount - prev.callcount;
                    stats.cpu_percent = sample_total / period;
                    stats.call_rate = sample_calls / period;
                    if (sample_calls !== 0)
                        stats.percall_time = (sample_total / sample_calls) * 1000000;
                    else
                        stats.percall_time = 0;
                } else {
                    stats.cpu_percent = 0;
                    stats.call_rate = 0;
                    stats.percall_time = 0;
                }
            }

            prev_ts = ts;
            prev_totals = totals;
            const final_stats = Object.keys(totals).map(key => totals[key]);
            final_stats.sort((a, b) => a[sortkey] < b[sortkey] ? 1 : -1);
            aioc.tpl.render('#prof-template', {stats: final_stats.slice(0, limit)});

            await aioc.util.sleep(1); /* XXX pull from UI */
        }
    })();
});
