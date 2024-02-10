document.addEventListener("DOMContentLoaded", function (){
    const pageType = document.querySelector("#page-type-value").textContent.trim();
    console.log("Page Type:", pageType);



    // Index Page
    if (pageType === 'index'){
        const createNewPostForm = document.getElementById("create-new-post-form")
        createNewPostForm.onsubmit = submitNewPost;
        displayPosts(1, '/api/posts/all/');
    }
    
    // Profile Page
    if (pageType === "profile"){
        const username = document.querySelector('#username').textContent;
        displayProfile(username);

        // readMoreLess();
    }

    // Following Page
    if (pageType == 'following'){
        displayPosts(1, '/api/posts/following/')
    }
});



async function displayProfile(username){

    // get logged in user:
    const loggedInUser = await getLoggedInUser();

    const profileContent = document.querySelector("#profile-content-header")
    fetch(`/api/profile/${username}/`)
        .then(response => response.json()) 
        .then(data => {
            profileContent.innerHTML = ''
            profileContent.innerHTML = `
                <h2 id="username">${data.username}</h2>
                <p id="followers-count">Followers: ${data.followers.length}</p>
                <p>Following: ${data.following.length}</p>
                <div id="feedback-animation"></div>
            `;

            console.log(data)
            console.log((loggedInUser))

            if (loggedInUser && loggedInUser.username !== data.username) {
                // If the logged-in user is not viewing their own profile, add the follow/unfollow button
                const followButton = document.createElement("button");
                followButton.id = "follow-button";
                followButton.className = data.followers.includes(loggedInUser.username) ? "btn btn-danger unfollow" : "btn btn-primary follow";
                followButton.textContent = data.followers.includes(loggedInUser.username) ? "Unfollow" : "Follow";
                profileContent.appendChild(followButton);

                console.log("INITIAL FOLLOW LOAD")
                console.log(followButton)

                followButton.addEventListener("click", function () {
                    handleFollowUnfollow(data.username, followButton);
                });
            }
        })

    // We then display the posts related to the user
    displayPosts(1, `/api/posts/user/${username}`);
};

function displayPosts(pageNumber, url) {
    const postListContainer = document.querySelector('.post-list');

    fetch(`${url}?page=${pageNumber}`)
        .then(response => response.json())
        .then(data => {
            console.log(data.posts[0])
            // Clear the existing content in the post list container
            postListContainer.innerHTML = '';

            // Check if there are posts to display
            if (data.posts.length > 0) {
                // console.log(data)
                // Loop through the posts and create HTML elements for each post
                data.posts.forEach(post => {
                    const postElement = document.createElement('div');
                    postElement.classList.add('post');
                    postElement.innerHTML = `
                        <div class="post-header" data-post-id="${post.id}">
                            <a href='/profile/${post.user.username}/'}><strong>${post.user.username}</strong></a>
                            <span>${formatTimestamp(post.timestamp)}</span>
                        </div>
                        <div class="post-content">
                            <p>${post.content}</p>
                        </div>
                        <div class="post-footer">
                            <div class="left-buttons">
                                <button class="like-button" data-post-id="${post.id}">
                                    ${post.user_has_liked ? 'Unlike' : 'Like'}
                                </button>
                                ${data.logged_in_user.username === post.user.username 
                                    ? `<button class="edit-button" data-post-id="${post.id}">Edit</button>` 
                                    : ''
                                }
                            </div>
                            <span class="likes-count">${post.likes_count}</span>
                        </div>
                    `;

                    
                    // Append the post container to the post list container
                    postListContainer.appendChild(postElement);

                    // Add event listener to the edit button for this post
                    const editButton = postElement.querySelector('.edit-button')
                    if (editButton){
                        editButton.addEventListener('click', () => editPost(postElement))
                    }

                    // Add event listener to the like button for this post
                    const likeButton = postElement.querySelector('.like-button');
                    likeButton.addEventListener('click', () => toggleLike(post.id, likeButton));

                    
                });

                // Create the Bootstrap pagination controls
                createPaginationControls(data.has_next, pageNumber, data.total_pages, url);

            } else {
                // Display a message if there are no posts
                postListContainer.innerHTML = 'No posts available.';
            }

            // // Create the Bootstrap pagination controls
            // createPaginationControls(data.has_next, pageNumber, data.total_pages, url);
            
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

function submitNewPost(event) {
    event.preventDefault(); // preventing the whole site from reloading

    // Getting the content
    const content = document.getElementById("content-input").value;
    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;
    const feedbackAnimation = document.getElementById("feedback-animation");

    // Using API to communicate with the backend and save the new post
    fetch("/api/posts/create/", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken, // Include the CSRF token
        },
        body: JSON.stringify({
            content: content
        })
    })
    .then(response => response.json())
    .then(data => {
        
        // Clear the form input field
        document.getElementById("create-new-post-form").reset();

        // send mesg
        handleFeedback(feedbackAnimation, data.success, data.message);

        if (data.success) {
            // After successfully creating the post, refresh the "All Posts" section
            displayPosts(1);
        }
        
        console.log(data);
    })
    .catch(error => {
        console.log(`ERROR HAPPENED: ${error}`);
        alert(error);
    });
}

function toggleLike(postId, likeButton) {
    // const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;
    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;
    console.log(csrfToken)

    const userHasLiked = likeButton.textContent.trim() === 'Unlike';

    likeButton.textContent = userHasLiked ? 'Like' : 'Unlike';

    fetch(`/api/posts/like/${postId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({ user_has_liked: userHasLiked }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update the likes count in the UI
            const likesCountElement = likeButton.parentElement.parentElement.querySelector('.likes-count');
            if (likesCountElement) {
                likesCountElement.textContent = data.likes_count;
            }
        } else {
            console.error('Failed to like/unlike the post:', data.message);

            // Revert the button text to its previous state if there was an error
            likeButton.textContent = userHasLiked ? 'Unlike' : 'Like';
        }
        console.log(data)
    })
    .catch(error => {
        console.error('Error:', error);

        // Revert the button text to its previous state if there was a network error
        likeButton.textContent = userHasLiked ? 'Unlike' : 'Like';
    });
}

function editPost(postElement) {
    // Find the post content element
    const postContent = postElement.querySelector('.post-content');
    
    // Save the original content
    const originalContent = postContent.innerText;

    // Create a textarea element
    const textarea = document.createElement('textarea');
    textarea.className = 'edit-textarea';
    textarea.value = originalContent; // Use the original content

    // Replace the post content with the textarea
    postContent.innerHTML = '';
    postContent.appendChild(textarea);

    // Create a "Cancel" button
    const cancelButton = document.createElement('button');
    cancelButton.innerText = 'Cancel';
    cancelButton.className = 'cancel-button';

    // Create a "Save" button
    const saveButton = document.createElement('button');
    saveButton.innerText = 'Save';
    saveButton.className = 'save-button';

    // Append the "Save" and "Cancel" buttons to the post content
    postContent.appendChild(cancelButton);
    postContent.appendChild(saveButton);

    // Add an event listener to the "Save" button
    saveButton.addEventListener('click', () => saveEditedPost(postElement, textarea));

    // Add an event listener to the "Cancel" button
    cancelButton.addEventListener('click', () => cancelEditPost(postElement, originalContent));
    
    // Add the 'editing' class to indicate editing mode
    postElement.classList.add('editing');

    // Hide the "Edit" button
    const editButton = postElement.querySelector('.edit-button');
    editButton.style.display = 'none';
}

function handleFollowUnfollow(username, button) {
    // Determine the action based on the button's class
    const action = button.classList.contains('unfollow') ? 'unfollow' : 'follow';

    console.log("Action to be made: " + action)
    // get the csrf token
    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    // Send an AJAX request to follow/unfollow the user
    fetch(`/api/profile/${username}/follow/`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken, // Include the CSRF token
        },
        body: JSON.stringify({ action }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.message === 'Followed successfully') {
            // Update button state and class
            button.textContent = 'Unfollow';
            button.classList.remove('follow');
            button.classList.add('unfollow');

            // Update follower count
            const followersCountElement = document.getElementById('followers-count');
            followersCountElement.textContent = "Followers: " + data.followers_count;
        } else if (data.message === 'Unfollowed successfully') {
            // Update button state and class
            button.textContent = 'Follow';
            button.classList.remove('unfollow');
            button.classList.add('follow');

            // Update follower count
            const followersCountElement = document.getElementById('followers-count');
            followersCountElement.textContent = "Followers: " + data.followers_count;
        }
        // Handle other cases or errors if necessary
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function saveEditedPost(postElement, textarea) {
    const postId = postElement.querySelector('.post-header').getAttribute('data-post-id');
    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;
    const feedbackAnimation = document.getElementById("feedback-animation");
    const newContent = textarea.value;

    // Check if the new content is empty
    if (!newContent.trim()) {
        handleFeedback(feedbackAnimation, false, 'Content cannot be empty');
        return;
    }

    // Send an AJAX request to update the post content
    fetch(`/api/posts/update/${postId}/`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({ content: newContent }),
    })
    .then(response => {
        if (response.status === 200) {
            return response.json();
        } else {
            throw new Error('Failed to update the post.');
        }
    })
    .then(data => {
        // Assuming the response contains the updated post data
        // Update the post content with the new content
        const postContent = postElement.querySelector('.post-content');
        postContent.innerHTML = data.content;

        // Restore the "Edit" button and exit editing mode
        const editButton = postElement.querySelector('.edit-button');
        editButton.style.display = 'inline';
        postElement.classList.remove('editing');

        // Provide feedback for success
        handleFeedback(feedbackAnimation, true, 'Post updated successfully');
    })
    .catch(error => {
        handleFeedback(feedbackAnimation, false, error.message);
    });
}

function cancelEditPost(postElement, originalContent) {
    // Find the post content element
    const postContent = postElement.querySelector('.post-content');

    // Clear the content inside the post content element
    postContent.innerHTML = '';

    // Restore the original content
    postContent.innerText = originalContent;

    // Add the "Edit" button back
    const editButton = postElement.querySelector('.edit-button');
    editButton.style.display = 'inline';

    // Remove the 'editing' class to exit editing mode
    postElement.classList.remove('editing');
}

function createPaginationControls(hasNext, currentPage, totalPages, url) {
    const postListContainer = document.querySelector('.post-list'); // Select the post list container
    const paginationContainer = document.createElement('nav');
    paginationContainer.classList.add('mt-3');
    paginationContainer.setAttribute('aria-label', 'Page navigation');

    const ul = document.createElement('ul');
    ul.classList.add('pagination', 'justify-content-center');

    // Define the pagination items based on your logic
    const paginationItems = [
        { label: '<<', page: 1, condition: currentPage > 1 },
        { label: '<', page: currentPage - 1, condition: currentPage > 1 },
        { label: `Page ${currentPage} of ${totalPages}`, page: currentPage, condition: true },
        { label: '>', page: currentPage + 1, condition: hasNext },
        { label: '>>', page: totalPages, condition: currentPage < totalPages },
    ];

    paginationItems.forEach(item => {
        if (item.condition) {
            const li = document.createElement('li');
            li.classList.add('page-item');
            const a = document.createElement('a');
            a.classList.add('page-link');
    
            // Set the data-page attribute directly
            a.setAttribute('data-page', item.page); // Use setAttribute
    
            // Set the href attribute
            a.href = `?page=${item.page}`;
    
            a.setAttribute('aria-label', item.label);
            a.innerHTML = item.label;
            li.appendChild(a);
            ul.appendChild(li);
        }
    });
    
    paginationContainer.appendChild(ul);
    
    // Append the new pagination controls to the post list container
    postListContainer.appendChild(paginationContainer);
    
    ul.querySelectorAll('.page-link').forEach(link => {
        link.addEventListener('click', (event) => {
            event.preventDefault(); // Uncomment this line to prevent default link behavior
    
            // Get the page number directly from the data-page attribute
            const page = parseInt(event.target.getAttribute('data-page'));
            if (!isNaN(page)) {
                history.pushState({}, '', `?page=${page}`);
                displayPosts(page, url);

                // Scroll to the top of the post container
                const postListContainer = document.querySelector('.post-list');
                postListContainer.scrollIntoView({ behavior: 'smooth'});
            }
        });
    });
    
}


/*************************
 *   HELPER FUNCTIONS   *
 *************************/
async function getLoggedInUser() {
    try {
        const response = await fetch('/get-logged-in-user/');
        if (response.status === 200) {
            const data = await response.json();
            const loggedInUser = data.user;
            return loggedInUser;
        } else {
            throw new Error('Failed to fetch user data');
        }
    } catch (error) {
        console.error('Error:', error);
        return null; // Handle the error appropriately
    }
}


// function getLoggedInUser() {
//     fetch('/get-logged-in-user/') // Replace with the correct URL
//         .then(response => response.json())
//         .then(data => {
//             // Handle the user data here
//             console.log('Logged-in user data:', data.user);
//             const loggedInUser = data.user;
//             return loggedInUser;
//         })
//         .catch(error => {
//             console.error('Error:', error);
//         })
// }
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const options = { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit', 
        hour12: true
    };
    return date.toLocaleDateString('en-US', options);
}

// function readMoreLess(){
//     const readMoreLinks = document.querySelectorAll(".read-more-link");
//     const readLessLinks = document.querySelectorAll(".read-less-link");

//     readMoreLinks.forEach(function(link) {
//         link.addEventListener("click", function(event) {
//             event.preventDefault();
//             const hiddenContent = this.nextElementSibling;
//             hiddenContent.style.display = "block";
//             this.style.display = "none";
//             hiddenContent.nextElementSibling.style.display = "inline"; // Display "Read Less" link
//         });
//     });

//     readLessLinks.forEach(function(link) {
//         link.addEventListener("click", function(event) {
//             event.preventDefault();
//             const expandedContent = this.previousElementSibling;
//             expandedContent.style.display = "none";
//             this.style.display = "none";
//             expandedContent.previousElementSibling.style.display = "inline"; // Display "Read More" link
//         });
//     });
// }

function handleFeedback(feedbackAnimation, success, message) {
    // // Clear the form input field
    // document.getElementById("create-new-post-form").reset();

    // Set appropriate CSS class based on success or error
    if (success) {
        feedbackAnimation.classList.remove("error-animation");
        feedbackAnimation.classList.add("success-animation");
    } else {
        feedbackAnimation.classList.remove("success-animation");
        feedbackAnimation.classList.add("error-animation");
    }

    // Show the message
    feedbackAnimation.style.display = 'block';
    feedbackAnimation.textContent = message;

    // Hide the message after a delay (e.g., 3 seconds)
    setTimeout(() => {
        feedbackAnimation.style.display = 'none';
    }, 3000); // Adjust the delay as needed
}
