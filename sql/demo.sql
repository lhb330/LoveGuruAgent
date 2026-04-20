CREATE TABLE public.t_ai_chat_message (
	id int8 DEFAULT nextval('ai_chat_message_id_seq'::regclass) NOT NULL,
	conversation_id varchar(64) NOT NULL, -- 对话ID
	message_type varchar(32) NOT NULL, -- 消息类型：USER、ASSISTANT、SYSTEM等
	"content" text NOT NULL, -- 消息内容
	"role" varchar(32) NOT NULL, -- 角色：user、assistant、system
	create_time timestamp DEFAULT CURRENT_TIMESTAMP NULL, -- 创建时间
	CONSTRAINT ai_chat_message_pkey PRIMARY KEY (id)
);
CREATE INDEX idx_ai_chat_message_conversation_id ON public.t_ai_chat_message USING btree (conversation_id);
COMMENT ON TABLE public.t_ai_chat_message IS '记录用户与系统对话信息';

-- Column comments

COMMENT ON COLUMN public.t_ai_chat_message.conversation_id IS '对话ID';
COMMENT ON COLUMN public.t_ai_chat_message.message_type IS '消息类型：USER、ASSISTANT、SYSTEM等';
COMMENT ON COLUMN public.t_ai_chat_message."content" IS '消息内容';
COMMENT ON COLUMN public.t_ai_chat_message."role" IS '角色：user、assistant、system';
COMMENT ON COLUMN public.t_ai_chat_message.create_time IS '创建时间';


-- 安装vector插件postgresql: https://github.com/pgvector/pgvector

-- 1. 先检查扩展是否在系统层面可见
SELECT name, default_version FROM pg_available_extensions WHERE name = 'vector';

-- 2. 如果上面返回结果，再创建扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 3. 验证安装成功
SELECT * FROM pg_extension WHERE extname = 'vector';

CREATE TABLE public.t_knowledge_embedding (
	id bigserial NOT NULL,
	doc_name varchar(255) NULL, -- 文件名称
	"content" text NULL, -- 文件切片内容
	metadata json NULL, -- 元数据
	embedding public.vector(1024) NULL, -- 向量(用的是阿里向量模型)
	CONSTRAINT t_knowledge_embedding_pkey PRIMARY KEY (id)
);
CREATE INDEX t_knowledge_embedding_index ON public.t_knowledge_embedding USING hnsw (embedding vector_cosine_ops);

-- Column comments

COMMENT ON COLUMN public.t_knowledge_embedding.doc_name IS '文件名称';
COMMENT ON COLUMN public.t_knowledge_embedding."content" IS '文件切片内容';
COMMENT ON COLUMN public.t_knowledge_embedding.metadata IS '元数据';
COMMENT ON COLUMN public.t_knowledge_embedding.embedding IS '向量';