from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import User, Category, Listing, Comment, Bid

############################################################################
def listing(request, id):
    listingData = Listing.objects.get(pk=id)
    isListingInWatchlist = request.user in listingData.watchlist.all()
    allComments = Comment.objects.filter(listing = listingData)
    isOwner = request.user.username == listingData.owner.username

    return render(request, "auctions/listing.html" ,{
        "listing": listingData,
        "isListingInWatchlist": isListingInWatchlist,
        "allComments": allComments,
        "isOwner": isOwner
    })

def categories(request):
    categories = Category.objects.all()
    return render(request, "auctions/categories.html", {"categories": categories})

def display_category(request, category_name):
    category = Category.objects.get(categoryName=category_name)
    listings = Listing.objects.filter(category=category)
    return render(request, "auctions/display_category.html", {"listings": listings})

def closeAuction(request, id):
    listingData = Listing.objects.get(pk=id)
    listingData.isActive = False
    listingData.save()
    isOwner = request.user.username == listingData.owner.username
    isListingInWatchlist = request.user in listingData.watchlist.all()
    allComments = Comment.objects.filter(listing = listingData)

    return render(request, "auctions/listing.html" ,{
        "listing": listingData,
        "isListingInWatchlist": isListingInWatchlist,
        "allComments": allComments,
        "isOwner": isOwner,
        "update": True,
        "message": "Congratulation! The Auction has been closed.",
        "user": request.user, 
        "isActive": listingData.isActive,
    })

def addBid(request, id):
    newBid = request.POST['newBid']
    listingData = Listing.objects.get(pk=id)
    isListingInWatchlist = request.user in listingData.watchlist.all()
    allComments = Comment.objects.filter(listing = listingData)
    isOwner = request.user.username == listingData.owner.username

    if int(newBid) > listingData.price.bid:
        updateBid = Bid(user=request.user, bid=int(newBid))
        updateBid.save()
        listingData.price = updateBid
        listingData.save()
        return render(request, "auctions/listing.html", {
            "listing": listingData,
            "message": "Bid was updated successfully",
            "update": True,
            "isOwner": isOwner,
            "isListingInWatchlist": isListingInWatchlist,
            "allComments": allComments
        })
    else:
         return render(request, "auctions/listing.html", {
            "listing": listingData,
            "message": "Bid update unsuccessful. Kindly submit a higher bid.",
            "update": False,
            "isOwner": isOwner,
            "isListingInWatchlist": isListingInWatchlist,
            "allComments": allComments
        })

def addComment(request, id):
    currentUser = request.user
    listingData = Listing.objects.get(pk=id)
    message = request.POST['newComment']

    newComment = Comment(
        author = currentUser,
        listing = listingData,
        message = message
    )
    newComment.save()
    return HttpResponseRedirect(reverse("listing", args=(id, )))

def displayWatchlist(request):
    currentUser = request.user
    listings = currentUser.listingWatchlist.all()
    return render(request, "auctions/watchlist.html", {
        "listings": listings
    })

def removeWatchlist(request, id):
    listingData = Listing.objects.get(pk=id)
    currentUser = request.user
    listingData.watchlist.remove(currentUser)
    return HttpResponseRedirect(reverse("listing", args=(id, )))

def addWatchlist(request, id):
    listingData = Listing.objects.get(pk=id)
    currentUser = request.user
    listingData.watchlist.add(currentUser)
    return HttpResponseRedirect(reverse("listing", args=(id, )))

def index(request):
    activeListings = Listing.objects.filter(isActive=True)
    allCategories = Category.objects.all()
    return render(request, "auctions/index.html", {
        "listings": activeListings ,
        "categories": allCategories,
    })

def displayCategory(request):
    if request.method == "POST":
        category_from_form = request.POST.get('category')
        if category_from_form:
            category = Category.objects.get(categoryName=category_from_form)
            active_listings = Listing.objects.filter(isActive=True, category=category)
            all_categories = Category.objects.all()
            return render(request, "auctions/index.html", {
                "listings": active_listings,
                "categories": all_categories,
                "selected_category": category_from_form,
            })

    # If there is an issue with the form submission or category retrieval, you may want to handle it here.
    return HttpResponse("Invalid form submission or category retrieval.")

def createListing(request):
    if request.method == "GET":
        allCategories = Category.objects.all()
        return render(request, "auctions/create.html", {
            "categories": allCategories,
        })
    else:
        title = request.POST["title"]
        description = request.POST["description"]
        imageUrl = request.POST["imageUrl"]
        price = request.POST["price"]
        category = request.POST["category"]

        currentUser = request.user

        categoryData = Category.objects.get(categoryName=category)

        bid = Bid(bid = int(price), user=currentUser)
        bid.save()
        newListing = Listing(
            title = title,
            description = description,
            imageUrl = imageUrl,
            price = bid,
            category = categoryData,
            owner = currentUser
        )
        newListing.save()
        return HttpResponseRedirect(reverse('index'))
    
        #  python manage.py makemigrations auctions
        #  python manage.py migrate

        #  python manage.py runserver

        # python manage.py createsuperuser
            # this typed for creating "The superuser account"
            # Username : Admin
            # Email address: sharmarajatraj1@gmail.com
            # Password : 3030
############################################################################

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
