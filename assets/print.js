// Make Plotly charts fit the page when printing / saving the page as a PDF.
//
// Plotly renders each chart at a fixed pixel width based on the on-screen
// container, and it does not re-layout when the browser switches to the
// (narrower) paper width for printing. Left alone, the charts overflow the
// PDF page. Here we re-lay-out every chart to a page-friendly width on
// `beforeprint` and restore the responsive on-screen sizing on `afterprint`.
// These events fire for both the "Download Page (PDF)" button (which calls
// window.print()) and a manual Ctrl/Cmd+P.

(function () {
    // ~ content width of a portrait Letter/A4 page at 96dpi with 1cm margins.
    // Kept slightly under both so nothing clips.
    var PRINT_WIDTH = 620;

    function resizePlots(width) {
        if (!window.Plotly) {
            return;
        }
        var plots = document.querySelectorAll(".js-plotly-plot");
        plots.forEach(function (gd) {
            if (width) {
                // Fix the chart to the page width for printing.
                window.Plotly.relayout(gd, { width: width, autosize: false });
            } else {
                // Restore responsive on-screen sizing.
                window.Plotly.relayout(gd, { autosize: true });
                window.Plotly.Plots.resize(gd);
            }
        });
    }

    window.addEventListener("beforeprint", function () {
        resizePlots(PRINT_WIDTH);
    });

    window.addEventListener("afterprint", function () {
        resizePlots(null);
    });
})();