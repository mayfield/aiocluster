"use strict";

const aioc = {
    util: {},
    api: {},
    tpl: {
        help: {}
    }
};

aioc.tpl.help.round = function(val, _kwargs) {
    const kwargs = _kwargs.hash;
    const prec = kwargs.precision !== undefined ? kwargs.precision : 0;
    const sval = Number(val.toFixed(prec)).toLocaleString();
    if (sval.indexOf('.') === -1) {
        return sval;
    } else {
        return sval.replace(/0+$/, '').replace(/\.$/, '');
    }
    
};

aioc.tpl.help.percent = function(val, _kwargs) {
    const sval = aioc.tpl.help.round(val, _kwargs);
    return new Handlebars.SafeString(sval + '&nbsp;<small>%</small>');
};

aioc.tpl.help.humantime = function(val) {
    return moment.duration(val, 'seconds').humanize();
};

aioc.tpl.help.time = function(val, _kwargs) {
    const buf = [];
    const n = Math.round(val);
    if (n > 86400) {
        buf.push(Math.floor(n / 86400).toLocaleString());
        buf.push('days, ');
    }
    buf.push(('0' + Math.floor((n % 86400) / 3600).toString()).slice(-2));
    buf.push(':');
    buf.push(('0' + Math.floor((n % 3600) / 60).toString()).slice(-2));
    buf.push(':');
    buf.push(('0' + (n % 60).toString()).slice(-2));
    return buf.join('');
};

aioc.tpl.help.humanbytes = function(val, _kwargs) {
    let units = [
        [1024 * 1024 * 1024 * 1024, 'TB'],
        [1024 * 1024 * 1024, 'GB'],
        [1024 * 1024, 'MB'],
        [1024, 'KB'],
        [0, ''],
    ];
    for (let i=0; i < units.length; i++) {
        const unit = units[i];
        if (Math.abs(val) >= unit[0]) {
            if (unit[0] !== 0)
                val /= unit[0];
            const s = aioc.tpl.help.round(val, _kwargs);
            return new Handlebars.SafeString([s, '&nbsp;<small>', unit[1],
                                             '</small>'].join(''));
        }
    }
};

aioc.tpl.help.humanint = function(val, _kwargs) {
    const units = [
        [1000000000000, 't'],
        [1000000000, 'b'],
        [1000000, 'm'],
        [1000, 'k'],
        [0, ''],
    ];
    for (let i=0; i < units.length; i++) {
        const unit = units[i];
        if (Math.abs(val) >= unit[0]) {
            if (unit[0] !== 0)
                val /= unit[0];
            const s = aioc.tpl.help.round(val, _kwargs);
            return new Handlebars.SafeString([s, '&nbsp;<small>', unit[1],
                                             '</small>'].join(''));
        }
    }
};

aioc.tpl.help.fixed = function(val, prec) {
    return val.toFixed(prec);
};

for (const key of Object.keys(aioc.tpl.help)) {
    Handlebars.registerHelper(key, aioc.tpl.help[key]);
}


/* Compile and render a handlebars template from an inline script.  The output
 * is placed right after the script tag holding the template. */
aioc.tpl.render = function(script_selector, tpl_context, _holder_tag) {
    const script = $(script_selector);
    let cache = script[0]._tpl_cache;
    if (cache === undefined) {
        cache = script[0]._tpl_cache = {};
        cache.template = Handlebars.compile(script.html());
        if (_holder_tag === undefined)
            _holder_tag = 'div';
        cache.holder = $(`<${_holder_tag}></${_holder_tag}>`);
        script.after(cache.holder);
    }
    cache.holder.html(cache.template(tpl_context));
};


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

aioc.api.request = function(method, path, data) {
    const request = {
        url: '/api/v1/' + path,
        method: method,
    };
    if (data !== undefined) {
        request.contentType = 'application/json';
        request.data = JSON.stringify(data);
    }
    return $.ajax(request);
}

aioc.api.get = function(path) {
    return aioc.api.request('GET', path);
};

aioc.api.put = function(path, data) {
    return aioc.api.request('PUT', path, data);
};
