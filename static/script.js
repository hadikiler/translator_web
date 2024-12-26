$(document).ready(function () {
    $('#alert').hide()
    $('#fileInput').on('change', function () {
        let fileNames = [];
        for (let i = 0; i < this.files.length; i++) {
            fileNames.push(this.files[i].name);
        }
        $('#fileName').text(fileNames.join(', '));
    });
    $('#uploadForm').on('submit', function (e) {
        e.preventDefault();
        let apiKey = $('#apiKey').val();
        let formData = new FormData(this);
        formData.append("apiKey", apiKey);
        $('#progressContainer').show();
        $('#downloadLink').hide()
        $('.loader').show()
        $('#alert').hide()

        $.ajax({
            url: '/upload/',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function (response) {
                $('#downloadFile').attr('href', `/media/${response['zip_file']}`);
                $('#downloadLink').show();
                $('.loader').hide()
            },
            error: function (response) {
                response = JSON.parse(response.responseText)
                $('#downloadFile').attr('href', `/media/${response['zip_file']}`);
                $('#alert').show().text(response['message'])
                $('#downloadLink').show();
                $('.loader').hide()
                clearInterval(interval)
            }
        });

        let interval = setInterval(function () {
            $.getJSON('/progress/', function (data) {
                let total = data.total;
                let remaining = data.remaining;
                let percent = Math.round(((total - remaining) / total) * 100);
                $('#progressText').text(percent + '%');
                $('#progressBar').css('width', percent + '%');
                if (remaining === 0) {
                    clearInterval(interval);
                }
            });
        }, 1000);
    });
});

window.addEventListener('beforeunload', function (e) {
    navigator.sendBeacon('/disconnect', JSON.stringify({ message: 'tab closed' }));
});
