"use strict";

var aioc = window.aioc || {};

aioc.conv = {
    megabytes: function(val) {
        return Math.round(val / 1024 / 1024).toString() + ' MB';
    },
    percent: function(val) {
        return Math.round(val).toString() + '%';
    },
    humantime: function(val) {
        return moment.duration(val, 'seconds').humanize();
    },
    humanint: function(val) {
        let units = [
            [1000000000000, 't'],
            [1000000000, 'b'],
            [1000000, 'm'],
            [1000, 'k'],
            [0, ''],
        ];
        let prec = 1;
        for (let i=0; i < units.length; i++) {
            let unit = units[i];
            if (Math.abs(val) >= unit[0]) {
                if (unit[0] !== 0)
                    val /= unit[0];
                let s = val.toFixed(prec).replace(/0+$/, '') + unit[1];
                return s.replace(/\.$/, '');
            }
        }
    }
};

Object.keys(aioc.conv).forEach(function(key) {
    Handlebars.registerHelper(key, aioc.conv[key]);
});


aioc.util = aioc.util || {};
aioc.util.sleep = function(seconds) {
    return new Promise(r => setTimeout(r, seconds * 1000));
};

    /* Emulate Python's asyncio.as_completed */
aioc.util.as_completed = function*(promises) {
    const pending = new Set(promises);
    for (const p of pending) {
        p.then(function resolved(v) {
            pending.delete(p);
            return v;
        }, function rejected(e) {
            pending.delete(p);
            throw e;
        });
    }
    while (pending.size) {
        yield Promise.race(pending);
    }
};
