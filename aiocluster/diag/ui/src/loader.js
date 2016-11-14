$(document).ready(function() {
    (async function() {
        let header = await $.get('templates/header.html');
        let tpl = $.templates(header);
        $('#header-holder').html(tpl.render({
            active_page_title: 'Processes XXX',
            inactive_pages: [{
                url: 'prof.html',
                title: 'Performance Profiler'
            }, {
                url: 'memory.html',
                title: 'Memory Tracker'
            }]
        }));
    })();
});
