import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .serializers import TripPlanRequestSerializer
from .services import build_trip_plan, RoutingError

@api_view(["GET"])
def health(request):
    return Response({"status": "ok"})

@api_view(["POST"])
def plan_trip(request):
    serializer = TripPlanRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    try:
        result = build_trip_plan(
            data["current_location"],
            data["pickup_location"],
            data["dropoff_location"],
            data["current_cycle_used"],
        )
        return Response(result)
    except RoutingError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except requests.RequestException:
        return Response(
            {"detail": "The free geocoding/routing service is temporarily unavailable. Please try again."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
