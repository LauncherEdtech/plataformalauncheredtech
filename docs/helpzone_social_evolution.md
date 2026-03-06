# HelpZone Social Evolution (MVP)

## Etapa 1 — Diagnóstico resumido
- O HelpZone social atual já possui feed, seguidores, comentários, stories, busca e perfil social.
- Havia desalinhamento entre endpoints usados no frontend (`/api/buscar`, `/api/seguir/:id`, `/api/notificacoes`) e rotas existentes no backend.
- O módulo já reutiliza User, XP, S3 upload e autenticação do ecossistema Launcher.

## Etapa 2 — Arquitetura de evolução (MVP incremental)
1. **Compatibilidade de API sem quebrar base existente**
   - Introduzir endpoints de compatibilidade consumidos pelos templates atuais.
2. **Gamificação social útil**
   - Conceder XP por ações que refletem estudo/comunidade: post, story, comentário, follow e post automático de progresso.
3. **Produto social focado em estudo**
   - Renomear stories para tema de rotina (`Sprint do Dia`).
   - Criar trilha de vídeos curtos em `EstudeVideos` usando posts de vídeo já existentes.
4. **Integração com dados reais de estudo**
   - Endpoint para criação de post automático de progresso (`/api/postar-progresso`).

## Etapa 3 — Implementação entregue
- Novos endpoints de compatibilidade:
  - `GET /helpzone/api/notificacoes`
  - `POST /helpzone/api/notificacao/<id>/lida|ler|marcar-lida`
  - `POST /helpzone/api/notificacoes/marcar-todas-lidas`
  - `POST /helpzone/api/seguir/<id>`
  - `GET /helpzone/api/buscar`
  - `GET /helpzone/api/ranking-seguidores`
  - `DELETE /helpzone/api/comentario/<id>/deletar`
- Novo endpoint de rotina/progresso:
  - `POST /helpzone/api/postar-progresso`
- Nova área visual:
  - `GET /helpzone/reels` + template `helpzone/reels.html` com experiência `EstudeVideos`.
- Melhorias de UX no feed:
  - Stories renomeado para `Sprint do Dia`.
  - Acesso direto para `EstudeVideos` na sidebar/mobile.
- Gamificação integrada:
  - XP social por ações úteis no HelpZone.
