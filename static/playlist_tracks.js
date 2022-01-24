
$('.add-track-to-playlist').click(addTrackToPlaylist)



async function addTrackToPlaylist() {
    const id = $(this).data('id')
    await axios.get(`/handle_add_tracks_to_playlist/${id}`)



}

const removeButtons = document.querySelectorAll('.add-track-to-playlist');

for (let btn of removeButtons) {
    btn.addEventListener('click', function (e) {
        e.target.remove();
        alert('added!')
    });



}



