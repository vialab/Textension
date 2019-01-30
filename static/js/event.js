/******************************************************************************
 * event.js
 * Instantiate all our interactions for digital object on /interact page
 * This is mostly the widget button functionality in our side bar
 *****************************************************************************/

$(document).ready(function() {
    $(".stage, html").css("background-color","rgb(" + bg_color[0] + "," + bg_color[1] + "," + bg_color[2] + ")")
    closeNav(); // start with tool bar closed
    // handle the resizing of the window and recalculate margins
    $(window).resize(mapBlockMesh);
    // click event listener for lines to be toggled opened or closed
    $(".img-block:not(.img-patch)").on("click", function() {
        if (getActiveMode() != "vertical") return; // proper mode needed
        let id = $(this).attr("id").replace("block", "patch");
        toggleSingleSpace($("#"+id.toString()+".img-patch"), false)
    });

    injectMetaData(); // insert the OCR text into the html elements
    drawOverlays(); // draw our graphs that the user can interact with
    $(".text-confidence").hide();

    // instantiate our OCR confidence highlight button
    $("#confidence").on("click", function() {
        if($(this).is(":checked")) {
            $(".text-confidence").show();            
        } else {
            $(".text-confidence").hide();            
        }
    });

    // drawUniqueness();
    // instantiate our uniqueness tool
    $("#uniqueness-range").hide();
    $("#uniqueness").on("click", function() {
        if($(this).is(":checked")) {
            openSpaces(false);
            setUniqueness( $("#uniqueness-range input").val() );
            $("#uniqueness-range").show();
            $(".switch").css("height", "15%");
        } else {
            $(".patch-box span.uniqueness-bar").height(0);
            $("#uniqueness-range").hide();
            $(".switch").css("height", "16%");
        }
    });

    // we use range sliders for things like year
    let rangeSlider = function(){
        let slider = $('.range-slider'),
            range = $('.range-slider__range'),
            value = $('.range-slider__value');
        slider.each(function(){
        
            value.each(function(){
            let value = $(this).prev().attr('value');
            $(this).html(value);
            });
        
            range.on('input', function(){
            $(this).next(value).html(this.value);
            });
        });
    };
    rangeSlider();

    // Ngram usage widget buttom
    $(".ngram-usage").hide();
    $("#ngram").on("click", function() {
        if($(this).is(":checked")) {
            openSpaces(false);            
            $(".ngram-usage").show();
        } else {
            $(".ngram-usage").hide();            
        }
    });

    // Maps widget button
    drawLocations();    
    $(".entity-location").hide();
    $("#entity-map-container").hide();
    $("#location").on("click", function() {
        if($(this).is(":checked")) {
            $(".entity-location").show();
            $("#entity-map-container").show();
        } else {
            $(".entity-location").hide();
            $("#entity-map-container").hide();
        }
        mapBlockMesh();
    });

    // Translation widget button
    $("#translate-text").on("click", function() {
        if($(this).is(":checked")) {
            if( $("#ocr-text").is(":checked") ) {
                $("#ocr-text").click();
            }
            $(".vis-container").each(function(i, $e) {
                let block_num = $(this).data("block");
                $(".img-patch-text", $e).each(function(idx) {
                    $(this).val(translation[block_num][idx]);
                });
            });
        } else {
            $(".img-patch-text").each(function(idx) {
                $(this).val("");
            });
        }
    });

    // OCR widget button
    $("#ocr-text").on("click", function() {
        if($(this).is(":checked")) {
            if($("#translate-text").is(":checked")) {
                $("#translate-text").click();
            }
            $(".vis-container").each(function(i, $e) {
                let block_num = $(this).data("block");
                $(".img-patch-text", $e).each(function(idx) {
                    console.log(ocr[block_num][idx]);
                    $(this).val(ocr[block_num][idx]);
                });
            });
        } else {
            $(".img-patch-text").each(function(idx) {
                $(this).val("");
            });
        }
    });

    // Pronoun replacement widget button {
    $("#replace-pronoun").on("click", function() {
        if($(this).is(":checked")) {
            $(".gender-pronoun").show();
        } else {
            fixPronouns();
            if($("#male-pronoun").is("checked")) {
                $("#male-pronoun").click();
            }
            if($("#female-pronoun").is("checked")) {
                $("#female-pronoun").click();
            }
            $(".gender-pronoun").hide();
        }
    });

    $("#male-pronoun").on("click", function() {
        if($(this).is(":checked")) {
            if($("#female-pronoun").is("checked")) {
                $("#female-pronoun").click();
            }
            replacePronouns(false);
        } else {
            fixPronouns();
        }
    });

    $("#female-pronoun").on("click", function() {
        if($(this).is(":checked")) {
            if($("#male-pronoun").is("checked")) {
                $("#male-pronoun").click();
            }
            replacePronouns(true);
        } else {
            fixPronouns();
        }
    });
    // } end of pronoun replacement buttons

    // ACTIVE TOOLS - tools that alter the left click functionality
    $("#draw-tool").on("click", function() {
        if($(this).is(":checked")) {
            setActiveMode("draw");
            $("canvas#draw-board").removeClass("overlay");
            $("#draw-options").show();
            if(!haslistener) init();
        } else {
            setActiveMode("");
            $("#draw-options").hide();            
        }
    });

    $(".img-block:not(.img-patch) img").on("click", function() {
        switch(getActiveMode()) {
            case "eraser":
                eraseWord($(this));
                break;
            case "horizontal":
                if($(this).hasClass("img-text")) {
                    let str_id = $(this).attr("id");
                    str_id = str_id.replace("text", "space");
                    toggleSingleSpace($("#"+str_id), true)
                }
                break;
            case "grammar":
            case "draw":
            case "vertical":
            default:
                return;
        }
    });

    $(".img-block:not(.img-patch) img").on("mousedown", function() {
        mouse_down = true;
        let action;
        switch(getActiveMode()) {
            case "define":
                action = defineWord;
                break;
            case "context":
                action = createContextMap;
                break;
            default:
                return;
        }
        timeout_id = setTimeout(action($(this)), 1000);
    }).on("mouseup mouseleave", function() {
        mouse_down = false;
        switch(getActiveMode()) {
            case "define":
                $(this).popover("hide");
                break;
            case "context":
                break;
            default:
                return;
        }
        clearTimeout(timeout_id);
    });
    // END ACTIVE TOOLS
    createMeshMap();
    mapBlockMesh();
    $("#vis-container").css("opacity", 1);
    $("#loading").removeClass("show");
});

function createMeshMap() {
    for(let i = 0; i < num_blocks; i++) {
        block_mesh.push([[99999999,99999999],[-1,-1]]);
        block_x.push(0);
        block_y.push(0);
    }
    $(".cell-grid .img-box").each(function(i, b) {
        let row = []
        $(".img-cell", $(b)).each(function(j, c) {
            row.push($(c));
            let data_block = $(c).data("block");
            if(data_block != "" || data_block == "0") {
                let block_num = parseInt(data_block);
                if(i <= block_mesh[block_num][0][1]) {
                    block_mesh[block_num][0][1] = i;
                    if(j < block_mesh[block_num][0][0]) {
                        block_mesh[block_num][0][0] = j;
                    }
                }
                if(i >= block_mesh[block_num][1][1]) {
                    block_mesh[block_num][1][1] = i;
                    if(j >= block_mesh[block_num][0][0]) {
                        block_mesh[block_num][1][0] = j;
                    }
                }
            }
        });
        mesh.push(row);
        $(this).data("img-width", $(this).width());
    });
    for(let i=0; i < block_mesh.length; i++) {
        block_x[i] = block_mesh[i][0][0];
        block_y[i] = block_mesh[i][0][1];
    }
    block_x = argsort(block_x);
    block_y = argsort(block_y);
}

function reinitializeWidgetEntities() {
    let $grid_rows = $(".img-box")
        , $first = $($grid_rows[0])
        , $last = $($grid_rows[$grid_rows.length-1])
        , stage_width = $first.width()
        , stage_height = $last.position().top + $last.height() - $first.position().top;
    $(".stage, .vis, .cell-grid").css("min-height", stage_height);
    $(".stage, .vis, .cell-grid").css("min-width", stage_width);
    let right_margin = $(".cell-grid").position().left + $(".cell-grid").width() - margin_size
        , left_margin = $(".cell-grid").position().left + margin_size;
    $("#context-map-container").css("left", right_margin);
    $("#entity-map-container").css("left", left_margin - $("#entity-map-container").width());
    // resize our drawing canvas as well, retaining all markings
    let canvas = document.getElementById('draw-board')
        , buffer = document.getElementById('buffer');
    buffer.width = stage_width;
    buffer.height = stage_height;
    buffer.getContext("2d").drawImage(canvas, 0, 0);
    canvas.width = stage_width;
    canvas.height = stage_height;
    canvas.getContext("2d").drawImage(buffer, 0, 0);
    $("#draw-board").width(canvas.width);
    $("#draw-board").height(canvas.height);
}

function resetBlockMesh() {
    for(let i=0; i < mesh.length; i++) {
        for(let j=0; j < mesh[i].length; j++) {
            $(mesh[i][j]).css("min-width", $(mesh[i][j]).data("img-width"));
        }
    }
    reinitializeWidgetEntities();
}

function resizeBlockMesh(block_num) {
    let min_x = block_mesh[block_num][0][0]
    , max_x = block_mesh[block_num][1][0]+1
    , $b = $("#vis-container-"+block_num)
    , space_size = $b.width();
    for(let i=min_x; i < max_x; i++) {
        space_size -= $(mesh[0][i]).data("img-width");
    }
    let dw = space_size / (max_x-min_x);
    for(let i=0; i < mesh.length; i++) {
        let $b = $(mesh[i][0]).parent();
        $b.width($b.data("img-width")+space_size);
        for(let j=min_x; j < max_x; j++) {
            let $cell = $(mesh[i][j]);
            $cell.css("min-width", $cell.data("img-width")+dw);
        }
    }

    let min_y = block_mesh[block_num][0][1]
        , max_y = block_mesh[block_num][1][1]+1;
    $b = $("#vis-container-"+block_num);
    space_size = $b.height();
    for(let i=min_y; i < max_y; i++) {
        space_size -= $(mesh[i][0]).parent().height();
    }
    let dh = space_size / (max_y-min_y);
    for(let i=min_y; i < max_y; i++) {
        let $b = $(mesh[i][0]).parent();
        $b.height($b.height()+dh);
    }
    reinitializeWidgetEntities();
}

function mapBlockMesh() {
    for(let j=0; j < block_mesh.length; j++) {
        let mesh_xy = block_mesh[j][0];
        let $cell = $(mesh[mesh_xy[1]][mesh_xy[0]]);
        let top_offset = $cell.parent().position().top
            , left_offset = $cell.parent().position().left + $cell.position().left;
        $("#vis-container-"+j).css({"top":top_offset});
        $("#vis-container-"+j).css({"left":left_offset});
    }
}