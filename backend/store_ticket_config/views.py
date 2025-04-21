from django.shortcuts import render
from rest_framework import viewsets
from .serializers import TickerSerializer
from .models import ticketConfig
from rest_framework.response import Response
from django.utils import timezone
from rest_framework.decorators import action
from django.db.models import Count

# Create your views here.
class TicketConfigViewSet(viewsets.ModelViewSet):
    queryset = ticketConfig.objects.all()
    serializer_class = TickerSerializer
    lookup_field = 'ticket_channel_id'  # 👈 Add this!

       # Override the update method to handle the PATCH request for status change
    def partial_update(self, request, *args, **kwargs):
        ticket_instance = self.get_object()  # Get the ticket instance based on the provided ticket ID
        
        # Ensure that the ticket status is part of the request
        status = request.data.get('status')
        if status:
            ticket_instance.status = status  # Update the status
            ticket_instance.save()  # Save the changes to the ticket instance
        
        return Response({'status': 'success', 'message': 'Ticket status updated successfully.'})

    @action(detail=True, methods=['post'], url_path='resolve')
    def resolve_ticket(self, request, ticket_channel_id=None):
        ticket = self.get_object()
        if ticket.status != 'resolved':
            ticket.status = 'resolved'
            ticket.resolved_at = timezone.now()

            mod_username=request.data.get('mod_username')
            mod_id=request.data.get('mod_id')
             # Ensure mod_username and mod_id are not None
            if not mod_username or not mod_id:
                return Response({'message': 'Moderator username and ID are required.'}, status=400)

            ticket.resolved_by_username = mod_username
            ticket.resolved_by_id = mod_id
            ticket.save()
            return Response({'message': 'Ticket marked as resolved.'}, status=200)
        return Response({'message': 'Ticket is already resolved.'}, status=200)
    
    @action(detail=False, methods=['get'], url_path='leaderboard')
    def leaderboard(self, request):
        top_mods = (
            ticketConfig.objects
            .filter(status='resolved')
            .values( 'resolved_by_username')
            .annotate(resolved_count=Count('id'))
            .order_by('-resolved_count')[:5]
        )
        
        # Return only the resolved_by_username and their resolved_count
        leaderboard_data = [
            {"resolved_by_username": mod['resolved_by_username'], "resolved_count": mod['resolved_count']}
            for mod in top_mods
        ]

        return Response(leaderboard_data)
     

