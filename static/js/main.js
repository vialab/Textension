$(document).ready(function() {
    $("#main-nav").peekaboo({
        offset_top: 60
        , scroll_threshold: 10
        , opaque_threshold_down: 5
        , opaque_threshold_up: 5
        , animation: true
        , hide_class: "slide-up"
        , fade_class: "fade-background"
        , hide_height_auto: true
    });
});