"use strict";

var aioc = window.aioc || {};
aioc.util = aioc.util || {};
aioc.api = aioc.api || {};

aioc.conv = {
    round: Math.round,
    percent: function(val) {
        return new Handlebars.SafeString(Math.round(val).toString() +
                                         '&nbsp;<small>%</small>');
    },
    humantime: function(val) {
        return moment.duration(val, 'seconds').humanize();
    },
    humanbytes: function(val) {
        let units = [
            [1024 * 1024 * 1024 * 1024, 'TB'],
            [1024 * 1024 * 1024, 'GB'],
            [1024 * 1024, 'MB'],
            [1024, 'KB'],
            [0, ''],
        ];
        let prec = 1;
        for (let i=0; i < units.length; i++) {
            let unit = units[i];
            if (Math.abs(val) >= unit[0]) {
                if (unit[0] !== 0)
                    val /= unit[0];
                let s = val.toFixed(prec).replace(/0+$/, '')
                s = s.replace(/\.$/, '');
                return new Handlebars.SafeString([s, '&nbsp;<small>', unit[1],
                                                 '</small>'].join(''));
            }
        }
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
                let s = val.toFixed(prec).replace(/0+$/, '');
                s = s.replace(/\.$/, '');
                return new Handlebars.SafeString([s, '&nbsp;<small>', unit[1],
                                                 '</small>'].join(''));
            }
        }
    },
    toFixed: function(val, prec) {
        return val.toFixed(prec);
    }
};

Object.keys(aioc.conv).forEach(function(key) {
    Handlebars.registerHelper(key, aioc.conv[key]);
});



aioc.util.sleep = async function(seconds) {
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


aioc.api.get = function(path) {
    return $.ajax({
        url: '/api/v1/' + path,
        method: 'GET'
    });
};


aioc.api.put = function(path, data) {
    return $.ajax({
        url: '/api/v1/' + path,
        method: 'PUT',
        contentType: 'application/json',
        data: JSON.stringify(data)
    });
};
