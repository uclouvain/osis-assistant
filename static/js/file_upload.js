/*
 *
 *   OSIS stands for Open Student Information System. It's an application
 *   designed to manage the core business of higher education institutions,
 *   such as universities, faculties, institutes and professional schools.
 *   The core business involves the administration of students, teachers,
 *   courses, programs and so on.
 *
 *   Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
 *
 *   This program is free software: you can redistribute it and/or modify
 *   it under the terms of the GNU General Public License as published by
 *   the Free Software Foundation, either version 3 of the License, or
 *   (at your option) any later version.
 *
 *   This program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU General Public License for more details.
 *
 *   A copy of this license - GNU General Public License - is available
 *   at the root of the source code of this program.  If not,
 *   see http://www.gnu.org/licenses/.
 *
 */

//***************************
//File upload
//***************************
$("#txt_file").on("change", function() {
    var file = this.files[0];
    fileName = file.name;
    $("#hdn_filename").val(fileName);
    if(fileName.length > 100){
        document.getElementById('error_modal_upload_alert').classList.remove('d-none');
        document.getElementById("error_modal_upload").innerHTML = "{% trans 'The length of filename may not exceed 100 characters.'%}";
        $("#txt_file").val('')
        $('#pnl_upload_error').remove();
        event.preventDefault();
        event.stopImmediatePropagation();
        return false;
    }
    else {
        document.getElementById('error_modal_upload_alert').classList.add('d-none');
        document.getElementById("error_modal_upload").innerHTML = "";
    }
    res = /.*[()%$,;:/=+].*/i.test(fileName);
    if(res)
        {
        document.getElementById('error_modal_upload_alert').classList.remove('d-none');
        document.getElementById("error_modal_upload").innerHTML = "{% trans 'Filename can not contains : ( ) % $ , ; : / = +'%}";
        $("#txt_file").val('')
        $('#pnl_upload_error').remove();
        event.preventDefault();
        event.stopImmediatePropagation();
        return false;
    }
    else {
        document.getElementById('error_modal_upload_alert').classList.add('d-none');
        document.getElementById("error_modal_upload").innerHTML = "";
    }
});

$('[id^="bt_load_doc_"]').click(function(event) {
    var target = $(event.target);
    var id = target.attr("id");
    var pos = id.indexOf('bt_load_doc_');
    var description = id.substring(pos + 12);
});
$("#bt_upload_document").click(function(event) {
    var target = $(event.target);
    var id = target.attr("id");
    var form = target.form;
    var description = $("#hdn_description").val();
    //Clear existing fields
    $('#hdn_file_' + $("#txt_file").val()).remove();
    $('#hdn_file_name_' + description).remove();
    $('#hdn_file_description_' + description).remove();
    var fileSelect = document.getElementById('txt_file');
    var files = fileSelect.files;
    var file = files[0];
    var data = new FormData();
    data.append('description', description);
    data.append('storage_duration', 0);
    data.append('content_type', file.type);
    data.append('filename', $("#txt_file").val());
    data.append('mandate_id', $("#hdn_current_mandate_id").val());
    var accepted_types = ['application/pdf'];
    if (file) {
        if ($.inArray(file.type, accepted_types) >= 0) {
            data.append('file', file);
            $.ajax({
                url: "{% url 'assistant_file_upload' %}",
                enctype: 'multipart/form-data',
                type: 'POST',
                data: data,
                processData: false,
                contentType: false,
                complete: function(xhr, statusText) {
                    var data_response=xhr.responseText;
                    var jsonResponse = JSON.parse(data_response);
                    window.location.reload(true);
                    alert(jsonResponse["message"]);
                }
            });
            return true;
        }
        else {
            document.getElementById('error_modal_upload_alert').classList.remove('d-none');
            document.getElementById("error_modal_upload").innerHTML = "{% trans 'You must select a PDF file'%}";
            $("#txt_file").val('')
            $('#pnl_upload_error').remove();
            event.preventDefault();
            event.stopImmediatePropagation();
            return false;
        }
    }
});
