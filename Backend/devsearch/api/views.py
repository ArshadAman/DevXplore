# Rest Framwrork Imports
from rest_framework import exceptions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from django.contrib.auth.hashers import make_password
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter

# Other Imports
from django.contrib.auth.models import User
from django.db import models
from users.models import Profile, Skill
from projects.models import Project, Review
from .serializers import ProfileSerializers, ProjectSerializers


@api_view(['GET'])
def getRoutes(request):
    routes = [
        {'GET': '/api/projects'},
        {'GET': '/api/projects/id'},
        {'POST': '/api/projects/id/vote'},
        {'POST': '/api/projects/id/vote'},
        {'POST': '/api/top-rated-projects/'},


        {'POST': '/api/users/token'},
        {'POST': '/api/users/token/refresh'},
        {'GET': '/api/users/get-profile'},
        {'GET': '/api/users/top-profile/'},
    ]

    return Response(routes)

# PROJECT RELATED VIEWS
# Read
class getProjects(generics.ListAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializers
    pagination_class = PageNumberPagination
    filter_backends = (SearchFilter, OrderingFilter)
    search_fields = ('title', 'desc', 'owner__name', 'owner__username')

@api_view(['GET'])
def topProjects(request):
    projects = Project.objects.all().order_by("-vote_ratio")[:4]
    serializer = ProjectSerializers(projects, many= True)
    return Response(serializer.data)

@api_view(['GET'])
def getProject(request, pk):
    project = Project.objects.get(id=pk)
    serializer = ProjectSerializers(project, many=True)
    return Response(serializer.data)

# Create
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def projectVote(request):
    user = request.user.profile
    data = request.data
    project = Project.objects.get(id = request.data['pro_id'])
    if project.owner == user:
        return Response({
            "Status": "You cannot vote your own project."
        })
    if user.id in project.reviewers:
        return Response({
            "Status": "You have already submmited the review for this project."
        })
    serializers = ProjectSerializers(project, many = False)
    review, created = Review.objects.get_or_create(
        owner = user,
        project = project,
    )
    review.value = data['value']
    review.body = data['body']
    review.save()
    project.getVotes

    return Response(serializers.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createProject(request):
    user = request.user.profile
    data = request.data

    new_project = Project.objects.create(
        owner = user,
        title = data['title'],
        desc = data['desc'],
        featured_image = data['featured_image'],
        demo_link = data['demo_link'],
        source_link = data['source_link'],
    )
    new_project.tags.set = data['tags']
    new_project.save()

    return Response({
        "Status": "Success",
    })

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def deleteProject(request):
    profile = request.user.profile
    id = request.data['id']
    try:
        project = profile.project_set.get(id=id)
        project.delete()
    except:
        return Response({
                "Error": "Some Error occured"
            }
        )
    return Response({
        "Status": "Project successfully deleted"
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def UpdateProject(request):
    profile =  request.user.profile
    data = request.data
    id = data['id']

    # Updating all the feilds
    title = data['title']
    desc = data['desc']
    featured_image = data['featured_image']
    demo_link = data['demo_link']
    source_link = data['source_link']
    tags = data['tags']
    try:
        project = profile.project_set.get(id = id)
        if not title == "":
            project.title = title
        project.desc = desc
        project.featured_image = featured_image
        demo_link = demo_link
        source_link = source_link
        tags = tags
    except:
        return Response({
            "Error": "Unable to find the project with that id in the database."
        })
    return Response({
        "Status": "Project Updated"
    })


# USER RELATED VIEWS
# For Login Make a Post Request to http://127.0.0.1:8000/api/users/token
# To logout user you need to delete the JWT token stored in the local storage

# Create
@api_view(['POST'])
def Signup(request):
    data = request.data
    username = data['username']
    try:
        user = User.objects.get(username=username)
        return Response({
                "Error": f'{user} already in the database'
            })
    except:
        new_user = User.objects.create(
            username = data['username'],
            first_name = data['name'],
            email = data['email'],
            password = make_password(data['password']),
        )
        new_user.save()
        return Response({
            "Status": "User Added"
        })

# UPDATE
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def UpdateProfile(request):
    user = request.user.profile
    data = request.data
    
    # Updating Username
    new_username = data['username']
    if User.objects.filter(username = new_username):
        # If username already exists
        return Response({
            "Error": "Username already exists try unique one."
        })

    elif not new_username == "":
        user.username = new_username
    elif new_username == "":
        pass

    # Updating name and email
    if data['name'] == "":
        user.name = user.name
    else:
        user.name = data['name']

    if data['email'] == "":
        user.email = user.email
    else:
        user.email = data['email']

    # Updating other parameters
    user.location = data['location']
    user.short_intro = data['short_intro']
    user.bio = data['bio']
    user.profile_image = data['profile_image']
    user.social_linkedin = data['linkedin']
    user.social_github = data['github']
    user.social_twitter = data['twitter']
    user.social_instagram = data['instagram']
    user.social_website = data['website']

    # Saving the details
    user.save()

    return Response({
        "Status": "Updated"
    })

# Read
class getProfiles(generics.ListAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializers
    pagination_class = PageNumberPagination
    filter_backends = (SearchFilter, OrderingFilter)
    search_fields = ('name', 'username', 'location', 'short_intro', 'bio')

@api_view(['GET'])
def getSingleProfile(request, pk):
    profile = Profile.objects.get(id=pk)
    projects = Project.objects.filter(owner_id = pk)
    project_serializer = ProjectSerializers(projects, many=True)
    serializer = ProfileSerializers(profile, many=False)
    return Response([serializer.data, project_serializer.data])

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getUserProfile(request):
    profile = Profile.objects.get(user = request.user)
    print(profile)
    projects = Project.objects.filter(owner_id = profile.id)
    # print(projects)
    project_serializer = ProjectSerializers(projects, many=True)
    serializer = ProfileSerializers(profile, many=False)
    return Response([serializer.data, project_serializer.data])
    

@api_view(['GET'])
def topProfile(request):
    top_profile = Profile.objects.annotate(num_project = models.Count('project')).order_by('-num_project')[:4]
    serializer = ProfileSerializers(top_profile, many=True)
    return Response(serializer.data)

# SKILLS CRUD
# Create
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addSkills(request):
    owner = request.user.profile
    data = request.data

    nameOfSkill = data['skill']
    description = data['description']

    new_skills = Skill(
        name = nameOfSkill,
        description = description,
    )
    new_skills.owner = owner
    new_skills.save()

    return Response({
        'Status': 'Success'
    })

# Edit
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def editSkills(request):
    profile = request.user.profile
    data = request.data

    id = data['id']
    nameOfSkill = data['new-name']
    description = data['description']

    try:
        skillToBeEdited = profile.skill_set.get(id=id)
        skillToBeEdited.name = nameOfSkill
        skillToBeEdited.description = description
        skillToBeEdited.save()
    except:
        return Response({
            "Error": "Some error occured"
        })

    return Response({
        'Status': 'Success'
    })

# Delete
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deleteSkills(request):
    profile = request.user.profile
    data = request.data

    id = data['id']

    try:
        skillToBeDeleted = profile.skill_set.get(id=id)
        skillToBeDeleted.delete()
    except:
        return Response({
            "Error": "Some error occured"
        })

    return Response({
        'Status': 'Successfully deleted'
    })
