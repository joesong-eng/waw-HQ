<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration {
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::table('users', function (Blueprint $table) {
            $table->enum('role', ['admin', 'owner', 'staff'])->default('owner')->after('password');
            $table->unsignedBigInteger('root_id')->nullable()->after('role')->comment('Owner ID for multi-tenant isolation');
            $table->tinyInteger('status')->default(1)->after('root_id');
            $table->string('line_id')->nullable()->after('status');
            $table->string('tg_id')->nullable()->after('line_id');

            $table->foreign('root_id')->references('id')->on('users')->onDelete('cascade');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('users', function (Blueprint $table) {
            $table->dropForeign(['root_id']);
            $table->dropColumn(['role', 'root_id', 'status', 'line_id', 'tg_id']);
        });
    }
};
