import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../theme/colors.dart';
import '../../theme/typography.dart';
import '../../theme/spacing.dart';
import '../../services/ai_agent_service.dart';
import '../../widgets/animations.dart';

class AiChatScreen extends ConsumerStatefulWidget {
  const AiChatScreen({super.key});

  @override
  ConsumerState<AiChatScreen> createState() => _AiChatScreenState();
}

class _AiChatScreenState extends ConsumerState<AiChatScreen> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final AiAgentService _aiService = AiAgentService();
  final List<_ChatMessage> _messages = [];
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _addInitialMessage();
  }

  void _addInitialMessage() {
    _messages.add(_ChatMessage(
      role: 'assistant',
      text: 'Bonjour ! Je suis CentralBot 🤖. Comment puis-je vous aider dans votre recherche immobilière aujourd\'hui ?',
      createdAt: DateTime.now(),
    ));
  }

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty || _isLoading) return;

    setState(() {
      _messages.add(_ChatMessage(
        role: 'user',
        text: text,
        createdAt: DateTime.now(),
      ));
      _isLoading = true;
      _controller.clear();
    });
    _scrollToBottom();

    final response = await _aiService.envoyerMessage(text);
    
    if (mounted) {
      setState(() {
        _isLoading = false;
        _messages.add(_parseMessage(response));
      });
      _scrollToBottom();
    }
  }

  _ChatMessage _parseMessage(String raw) {
    // Extraction simplifiée du tag [PROPRIETE:id|titre|image|prix|ville]
    final regExp = RegExp(r'\[PROPRIETE:([^\]]+)\]');
    final match = regExp.firstMatch(raw);
    
    if (match == null) {
      return _ChatMessage(role: 'assistant', text: raw, createdAt: DateTime.now());
    }

    final payload = match.group(1)!;
    final parts = payload.split('|');
    final cleanText = raw.replaceFirst(match.group(0)!, '').trim();

    if (parts.length < 5) {
      return _ChatMessage(role: 'assistant', text: cleanText, createdAt: DateTime.now());
    }

    return _ChatMessage(
      role: 'assistant',
      text: cleanText,
      createdAt: DateTime.now(),
      propertyData: {
        'id': parts[0],
        'title': parts[1],
        'image': parts[2],
        'price': parts[3],
        'city': parts[4],
      },
    );
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Assistant Intelligent'),
        backgroundColor: Colors.white,
        elevation: 0.5,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, color: AppColors.textPrimary, size: 20),
          onPressed: () => context.pop(),
        ),
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(AppSpacing.md),
              itemCount: _messages.length,
              itemBuilder: (context, index) => _ChatBubble(message: _messages[index]),
            ),
          ),
          if (_isLoading)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 8),
              child: SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)),
            ),
          _buildInput(),
        ],
      ),
    );
  }

  Widget _buildInput() {
    return Container(
      padding: EdgeInsets.fromLTRB(AppSpacing.md, 8, AppSpacing.md, MediaQuery.of(context).padding.bottom + 8),
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(top: BorderSide(color: AppColors.border, width: 0.5)),
      ),
      child: Row(
        children: [
          Expanded(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              decoration: BoxDecoration(
                color: AppColors.surfaceVariant,
                borderRadius: BorderRadius.circular(24),
              ),
              child: TextField(
                controller: _controller,
                onSubmitted: (_) => _send(),
                decoration: const InputDecoration(
                  hintText: 'Rechercher par description...',
                  border: InputBorder.none,
                ),
              ),
            ),
          ),
          const SizedBox(width: 8),
          Container(
            decoration: BoxDecoration(
              gradient: AppColors.primaryGradient,
              shape: BoxShape.circle,
            ),
            child: IconButton(
              onPressed: _send,
              icon: const Icon(Icons.send_rounded, color: Colors.white, size: 20),
            ),
          ),
        ],
      ),
    );
  }
}

class _ChatMessage {
  final String role;
  final String text;
  final DateTime createdAt;
  final Map<String, String>? propertyData;

  _ChatMessage({required this.role, required this.text, required this.createdAt, this.propertyData});
}

class _ChatBubble extends StatelessWidget {
  final _ChatMessage message;
  const _ChatBubble({required this.message});

  @override
  Widget build(BuildContext context) {
    final isAssistant = message.role == 'assistant';
    return Align(
      alignment: isAssistant ? Alignment.centerLeft : Alignment.centerRight,
      child: Column(
        crossAxisAlignment: isAssistant ? CrossAxisAlignment.start : CrossAxisAlignment.end,
        children: [
          if (message.propertyData != null) _buildPropertyCard(context),
          Container(
            margin: const EdgeInsets.only(bottom: 12),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
            decoration: BoxDecoration(
              color: isAssistant ? Colors.white : AppColors.primary,
              borderRadius: BorderRadius.circular(16).copyWith(
                bottomLeft: isAssistant ? const Radius.circular(0) : const Radius.circular(16),
                bottomRight: isAssistant ? const Radius.circular(16) : const Radius.circular(0),
              ),
              boxShadow: AppColors.cardShadow,
            ),
            child: Text(
              message.text,
              style: TextStyle(
                color: isAssistant ? AppColors.textPrimary : Colors.white,
                fontSize: 14,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPropertyCard(BuildContext context) {
    final data = message.propertyData!;
    return GestureDetector(
      onTap: () => context.push('/property/${data['id']}'),
      child: Container(
        width: 220,
        margin: const EdgeInsets.only(bottom: 8),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          boxShadow: AppColors.cardShadow,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ClipRRect(
              borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
              child: Image.network(
                data['image'] ?? '',
                height: 100,
                width: double.infinity,
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => Container(color: AppColors.surfaceVariant, height: 100),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(8.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(data['title'] ?? '', style: AppTypography.titleSmall.copyWith(fontSize: 13), maxLines: 1),
                  Text('${data['price']} XAF', style: TextStyle(color: AppColors.primary, fontWeight: FontWeight.bold, fontSize: 12)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
