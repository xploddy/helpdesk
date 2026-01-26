import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  SafeAreaView,
  Alert,
} from 'react-native';
import { ticketService } from '../services/api';

export const TicketDetailScreen = ({ route, navigation }) => {
  const { ticketId } = route.params;
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTicket();
  }, []);

  const loadTicket = async () => {
    setLoading(true);
    try {
      const data = await ticketService.getTicket(ticketId);
      setTicket(data);
    } catch (error) {
      Alert.alert('Erro', 'Não foi possível carregar o ticket');
    } finally {
      setLoading(false);
    }
  };

  const handleResolve = async () => {
    Alert.alert('Confirmar', 'Marcar ticket como resolvido?', [
      { text: 'Cancelar', style: 'cancel' },
      {
        text: 'Confirmar',
        onPress: async () => {
          try {
            await ticketService.resolveTicket(ticketId);
            loadTicket();
            Alert.alert('Sucesso', 'Ticket marcado como resolvido');
          } catch (error) {
            Alert.alert('Erro', error.message);
          }
        },
      },
    ]);
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  if (!ticket) {
    return (
      <View style={styles.centerContainer}>
        <Text>Ticket não encontrado</Text>
      </View>
    );
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'Aberto':
        return '#FF6B6B';
      case 'Em andamento':
        return '#FFA500';
      case 'Resolvido':
        return '#4ECDC4';
      default:
        return '#999';
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'Baixa':
        return '#4ECDC4';
      case 'Media':
        return '#FFA500';
      case 'Alta':
        return '#FF6B6B';
      case 'Critica':
        return '#8B0000';
      default:
        return '#999';
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.content}>
        <View style={styles.header}>
          <Text style={styles.title}>{ticket.title}</Text>
          <View
            style={[
              styles.statusBadge,
              { backgroundColor: getStatusColor(ticket.status) },
            ]}
          >
            <Text style={styles.statusText}>{ticket.status}</Text>
          </View>
        </View>

        <View style={styles.infoSection}>
          <View style={styles.infoRow}>
            <Text style={styles.label}>Categoria:</Text>
            <Text style={styles.value}>{ticket.category}</Text>
          </View>

          <View style={styles.infoRow}>
            <Text style={styles.label}>Prioridade:</Text>
            <View
              style={[
                styles.priorityBadge,
                { backgroundColor: getPriorityColor(ticket.priority) },
              ]}
            >
              <Text style={styles.priorityText}>{ticket.priority}</Text>
            </View>
          </View>

          <View style={styles.infoRow}>
            <Text style={styles.label}>Criado em:</Text>
            <Text style={styles.value}>
              {new Date(ticket.created_at).toLocaleDateString('pt-BR')}
            </Text>
          </View>

          {ticket.assigned_to && (
            <View style={styles.infoRow}>
              <Text style={styles.label}>Atribuído para:</Text>
              <Text style={styles.value}>{ticket.assigned_to.username}</Text>
            </View>
          )}
        </View>

        <View style={styles.descriptionSection}>
          <Text style={styles.sectionTitle}>Descrição</Text>
          <Text style={styles.description}>{ticket.description}</Text>
        </View>

        {ticket.comments && ticket.comments.length > 0 && (
          <View style={styles.commentsSection}>
            <Text style={styles.sectionTitle}>
              Comentários ({ticket.comments.length})
            </Text>
            {ticket.comments.map((comment) => (
              <View key={comment.id} style={styles.comment}>
                <Text style={styles.commentAuthor}>
                  {comment.author.username}
                </Text>
                <Text style={styles.commentDate}>
                  {new Date(comment.created_at).toLocaleDateString('pt-BR')}
                </Text>
                <Text style={styles.commentContent}>{comment.content}</Text>
              </View>
            ))}
          </View>
        )}
      </ScrollView>

      {ticket.status !== 'Resolvido' && ticket.status !== 'Fechado' && (
        <View style={styles.footer}>
          <TouchableOpacity style={styles.button} onPress={handleResolve}>
            <Text style={styles.buttonText}>Marcar como Resolvido</Text>
          </TouchableOpacity>
        </View>
      )}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    flex: 1,
    padding: 15,
  },
  header: {
    marginBottom: 20,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  statusBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 15,
  },
  statusText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  infoSection: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 15,
    marginBottom: 15,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
  },
  value: {
    fontSize: 14,
    color: '#333',
  },
  priorityBadge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  priorityText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  descriptionSection: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 15,
    marginBottom: 15,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  description: {
    fontSize: 14,
    color: '#666',
    lineHeight: 22,
  },
  commentsSection: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 15,
    marginBottom: 15,
  },
  comment: {
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  commentAuthor: {
    fontSize: 13,
    fontWeight: 'bold',
    color: '#333',
  },
  commentDate: {
    fontSize: 11,
    color: '#999',
    marginTop: 2,
  },
  commentContent: {
    fontSize: 13,
    color: '#666',
    marginTop: 8,
    lineHeight: 20,
  },
  footer: {
    padding: 15,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#eee',
  },
  button: {
    backgroundColor: '#007AFF',
    paddingVertical: 14,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
